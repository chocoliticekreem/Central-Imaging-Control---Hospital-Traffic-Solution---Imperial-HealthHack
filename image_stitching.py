import cv2
import numpy as np
from typing import Tuple, Optional

class ImageStitcher:
    def __init__(self, min_matches: int = 10, ransac_threshold: float = 4.0):
        """
        Initialize the image stitcher.
        
        Args:
            min_matches: Minimum number of feature matches to confirm overlap
            ransac_threshold: RANSAC threshold for homography estimation
        """
        self.min_matches = min_matches
        self.ransac_threshold = ransac_threshold
        self.orb = cv2.ORB_create(nfeatures=5000)
    
    def find_features(self, image: np.ndarray) -> Tuple[list, np.ndarray]:
        """Detect and compute ORB features in the image."""
        # Convert to grayscale for better feature detection
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        keypoints, descriptors = self.orb.detectAndCompute(gray, None)
        return keypoints, descriptors
    
    def match_features(self, desc1: np.ndarray, desc2: np.ndarray) -> list:
        """Match features between two images using BFMatcher."""
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        matches = bf.knnMatch(desc1, desc2, k=2)
        
        # Apply Lowe's ratio test to filter good matches
        good_matches = []
        for match_pair in matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < 0.75 * n.distance:
                    good_matches.append(m)
        
        return good_matches
    
    def verify_overlap(self, img1: np.ndarray, img2: np.ndarray, 
                       kp1: list, kp2: list, matches: list) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Verify if two images have a valid overlapping region.
        
        Args:
            img1, img2: Input images as matrices
            kp1, kp2: Keypoints for each image
            matches: Feature matches between images
        
        Returns:
            (is_overlap, homography_matrix)
        """
        if len(matches) < self.min_matches:
            return False, None
        
        # Extract matched points
        src_pts = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
        
        # Compute homography using RANSAC
        H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, self.ransac_threshold)
        
        if H is None:
            return False, None
        
        # Check if homography is valid (not too much distortion)
        inlier_count = np.sum(mask)
        inlier_ratio = inlier_count / len(matches)
        
        is_valid = inlier_ratio > 0.3 and inlier_count >= self.min_matches
        
        return is_valid, H if is_valid else None
    
    def stitch_images(self, img1: np.ndarray, img2: np.ndarray, 
                     H: np.ndarray) -> np.ndarray:
        """
        Stitch two images together using the homography matrix.
        Non-overlapping regions are filled with black.
        
        Args:
            img1: First image (to be warped)
            img2: Second image (reference)
            H: Homography matrix from img1 to img2's coordinate system
        
        Returns:
            Stitched image with black padding
        """
        h1, w1 = img1.shape[:2]
        h2, w2 = img2.shape[:2]
        
        # Get corners of img1 after warping to determine canvas size
        corners = np.float32([[[0, 0], [w1, 0], [0, h1], [w1, h1]]])
        warped_corners = cv2.perspectiveTransform(corners, H)[0]
        
        # Calculate bounding box
        x_min = min(0, warped_corners[:, 0].min())
        y_min = min(0, warped_corners[:, 1].min())
        x_max = max(w2, warped_corners[:, 0].max())
        y_max = max(h2, warped_corners[:, 1].max())
        
        canvas_width = int(x_max - x_min)
        canvas_height = int(y_max - y_min)
        
        # Adjust homography for canvas offset
        H_adjusted = H.copy()
        H_adjusted[0, 2] -= x_min
        H_adjusted[1, 2] -= y_min
        
        # Warp img1 with adjusted homography
        warped_img1 = cv2.warpPerspective(img1, H_adjusted, (canvas_width, canvas_height))
        
        # Create output canvas with black background
        stitched = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)
        
        # Place img2 at correct offset
        y2_offset = int(-y_min)
        x2_offset = int(-x_min)
        stitched[y2_offset:y2_offset+h2, x2_offset:x2_offset+w2] = img2
        
        # Blend overlapping region
        mask_warped = (warped_img1 != 0).any(axis=2)
        mask_stitched = (stitched != 0).any(axis=2)
        overlap_mask = mask_stitched & mask_warped
        
        # Blend where both images exist
        if np.any(overlap_mask):
            stitched[overlap_mask] = cv2.addWeighted(stitched[overlap_mask], 0.5, warped_img1[overlap_mask], 0.5, 0)
        
        # Place warped image where only it exists
        no_overlap = mask_warped & ~mask_stitched
        if np.any(no_overlap):
            stitched[no_overlap] = warped_img1[no_overlap]
        
        # Non-overlapping regions remain black (already initialized to 0)
        
        return stitched
    
    def calculate_quality_score(self, img1: np.ndarray, img2: np.ndarray, 
                               kp1: list, kp2: list, matches: list, 
                               H: Optional[np.ndarray]) -> float:
        """
        Calculate quality score for stitching configuration.
        Higher score = better stitching quality.
        """
        if H is None or len(matches) == 0:
            return 0.0
        
        # Extract matched points
        src_pts = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
        
        # Compute homography to get inliers
        _, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, self.ransac_threshold)
        
        inlier_count = np.sum(mask)
        match_ratio = inlier_count / len(matches) if matches else 0
        
        # Score: number of inlier matches * match quality ratio
        score = inlier_count * match_ratio
        
        return score
    
    def process(self, img1: np.ndarray, img2: np.ndarray) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Complete stitching pipeline: detect overlap and stitch if valid.
        Automatically tries both image orders and selects the best configuration.
        
        Args:
            img1, img2: Input images as numpy arrays
        
        Returns:
            (success, stitched_image)
        """
        # Find features
        kp1, desc1 = self.find_features(img1)
        kp2, desc2 = self.find_features(img2)
        
        if desc1 is None or desc2 is None:
            print("No descriptors found in one or both images")
            return False, None
        
        best_score = 0.0
        best_result = None
        best_config = None
        
        # Configuration 1: Stitch img1 onto img2
        matches_1to2 = self.match_features(desc1, desc2)
        is_overlap_1to2, H_1to2 = self.verify_overlap(img1, img2, kp1, kp2, matches_1to2)
        
        score_1to2 = self.calculate_quality_score(img1, img2, kp1, kp2, matches_1to2, H_1to2)
        
        if is_overlap_1to2 and score_1to2 > best_score:
            best_score = score_1to2
            best_result = self.stitch_images(img1, img2, H_1to2)
            best_config = "img1 → img2"
        
        # Configuration 2: Stitch img2 onto img1 (reverse order)
        matches_2to1 = self.match_features(desc2, desc1)
        is_overlap_2to1, H_2to1 = self.verify_overlap(img2, img1, kp2, kp1, matches_2to1)
        
        score_2to1 = self.calculate_quality_score(img2, img1, kp2, kp1, matches_2to1, H_2to1)
        
        if is_overlap_2to1 and score_2to1 > best_score:
            best_score = score_2to1
            best_result = self.stitch_images(img2, img1, H_2to1)
            best_config = "img2 → img1"
        
        if best_result is not None:
            print(f"Frame stitched - Config: {best_config} (score: {best_score:.2f}, matches: {len(matches_1to2) if is_overlap_1to2 else len(matches_2to1)})")
            return True, best_result
        
        print(f"No valid overlap - img1→img2: {len(matches_1to2)} matches, img2→img1: {len(matches_2to1)} matches")
        return False, None


def main():
    """Example usage of the ImageStitcher class."""
    # Load images
    img1 = cv2.imread(r'C:\Users\harve\OneDrive\Desktop\1000163968.jpg')
    img2 = cv2.imread(r'C:\Users\harve\OneDrive\Desktop\1000163969.jpg')
    
    if img1 is None or img2 is None:
        print("Error: Could not load images")
        return
    
    # Create stitcher
    stitcher = ImageStitcher(min_matches=10)
    
    # Process
    success, stitched = stitcher.process(img1, img2)
    
    if success:
        cv2.imwrite('stitched_result.jpg', stitched)
        print("Stitched image saved as 'stitched_result.jpg'")
    else:
        print("No valid overlap found between images")


if __name__ == "__main__":
    main()
