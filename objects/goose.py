import random 
import cv2 

import os

class Goose:
    """
    Represents a goose to catch
    """
    def __init__(self, xLimit: int, yLimit: int):
        IMAGE_PATH = os.path.join(os.getcwd(), 'objects', 'assets', 'goose.png')
        hd_image = cv2.imread(IMAGE_PATH, cv2.IMREAD_UNCHANGED)
        
        self.curPos = [random.randint(15, xLimit - 15), yLimit]
        self.nextPos = [0, 0]

        self.size = int(xLimit * 0.1)
        self.image = cv2.resize(hd_image, (self.size, self.size))
    
    def is_passed_border(self, xLimit: int, yLimit: int) -> bool: 
        """
        Check whether this goose has passed the border given
        
        Return `True` if the object's `curPos[0]` (x coordinate) is 
        greater than the given `xLimit`, or if the object's `curPos[1]` 
        (y coordinate) is smaller than the given `yLimit`
        """
        if (self.curPos[0] > xLimit or self.curPos[1] < yLimit):
            return True 

        return False 
    
    def set_next_position(self, speed: tuple[int, int]):
        """
        Set the next position of the object based on the speed
        """
        self.nextPos[0] = self.curPos[0] + speed[0]
        self.nextPos[1] = self.curPos[1] - speed[1] 

        self.curPos = self.nextPos 

    def get_offset(self):
        x_offset = self.curPos[0]
        y_offset = self.curPos[1]
        x_end = x_offset + self.image.shape[1]
        y_end = y_offset + self.image.shape[0]
        return y_offset, y_end, x_offset, x_end 
