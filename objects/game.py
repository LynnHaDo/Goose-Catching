from . import Goose

# Import modules for rendering video
import cv2
import time 
import numpy as np
import math 

# Import mediapipe modules
import mediapipe.python.solutions.hands as mp_hands
import mediapipe.python.solutions.drawing_utils as mp_drawing 
import mediapipe.python.solutions.drawing_styles as drawing_styles

# Set up the model
model = mp_hands.Hands(
    static_image_mode = False, 
    max_num_hands=1, 
    min_detection_confidence=0.6
)

class Game:
    """
    Represents a game object with several functionalities
    """
    def __init__(self, title):
        self.title = title # title of the game

        self.geese = [] # list of geese currently in the game
        
        self.lives = 20 # say we allow 20 lives at the start of the game
        self.score = 0 
        self.speed = [0, 5] # the speed by which objects are moving
        self.goose_rate = 0.5 # rate by which the geese are generated
        self.difficulty_level = 1 
        self.game_over = False 

        self.curFrame = 0
        self.prevFrame = 0 
        self.delta_time = 0
        self.next_goose_time = 0

        # Index finger movement 
        self.index_movement = np.array([[]], np.int32)
        self.index_movement_length = 19
    
    def create_goose(self):
        """
        Create a new goose
        """
        goose = Goose(self.xLimit, self.yLimit)
        self.geese.append(goose)
    
    def move_geese(self, img):
        """
        Move the geese created
        """
        for goose in self.geese: 
            if goose.is_passed_border(self.xLimit, 80):
                self.lives -= 1 
                self.geese.remove(goose)
            
            y_offset, y_end, x_offset, x_end  = goose.get_offset() 
            if y_end <= img.shape[0] and x_end <= img.shape[1]:
                b, g, r, a = cv2.split(goose.image)
                a = a/255.0 
                goose_rgb = cv2.merge([b*a, g*a, r*a])
                bg = img[y_offset:y_end, x_offset:x_end,:]
                bg_b, bg_g, bg_r = cv2.split(bg)
                bg = cv2.merge([bg_b * (1 - a), bg_g * (1 - a), bg_r * (1 - a)])
                cv2.add(goose_rgb, bg, bg) 
                img[y_offset:y_end, x_offset:x_end,:] = bg

            goose.set_next_position(self.speed)
    
    def distance(self, obj1: tuple[int, int], obj2: tuple[int, int]) -> int:
        """
        Helper to calculate the distance between 2 objects
        """
        x1 = obj1[0]
        x2 = obj2[0]

        y1 = obj1[1]
        y2 = obj2[1]

        d = math.sqrt(pow(x1 - x2, 2) + pow(y1 - y2, 2))
        return int(d)
    
    def start(self):
        # Start the video
        cap = cv2.VideoCapture(0)

        while (cap.isOpened()):
            self.xLimit = int(cap.get(3)) # get width
            self.yLimit = int(cap.get(4)) # get height

            success, img = cap.read() # read a frame

            if not success:
                continue # skip to the next frame 
                
            h, w, c = img.shape
            # Convert to RGB
            img = cv2.cvtColor(cv2.flip(img, 1), cv2.COLOR_BGR2RGB)
            img.flags.writeable = False

            # Detect the results
            result = model.process(img)
            # Converting back the RGB image to BGR
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

            # Draw the divider 
            cv2.line(img, (0, 80), (w, 80), (118, 62, 250), 3)

            # Handle events when the hand is captured on the screen
            if result.multi_hand_landmarks:
                hand_landmarks_list = result.multi_hand_landmarks
                # Loop through 21 landmarks
                for hand_landmarks in hand_landmarks_list:
                    # Visualize the landmarks
                    mp_drawing.draw_landmarks(
                        img, 
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS, 
                        drawing_styles.get_default_hand_landmarks_style(),
                        drawing_styles.get_default_hand_connections_style()
                    )

                    # Catch the movement of the index finger, and 
                    if hand_landmarks.landmark:
                        index_landmark = hand_landmarks.landmark[8] 
                        # Get the position
                        index_pos = (int(index_landmark.x * w), int(index_landmark.y * h))
                        cv2.circle(img, index_pos, 18, (28, 49, 235), -1)

                        self.index_movement = np.append(self.index_movement, index_pos)

                        while len(self.index_movement) >= self.index_movement_length:
                            self.index_movement = np.delete(self.index_movement, len(self.index_movement) - self.index_movement_length, 0)
                    
                        for goose in self.geese:
                            d = self.distance(goose.curPos, index_pos)
                            if (d < goose.size):
                                self.score += 100 
                                self.geese.remove(goose)

            # Unlock a new level
            if self.score > 0 and self.score % 1000 == 0: 
                self.difficulty_level = int((self.score / 1000) + 1)
                self.goose_rate = self.difficulty_level * 0.3 
                self.speed[0] = self.speed[0] * self.difficulty_level 
                self.speed[1] = int(self.speed[1] * self.difficulty_level * 0.2)
            
            if self.lives <= 0: 
                self.game_over = True 

            self.index_movement = self.index_movement.reshape((-1, 1, 2))
            # draw the movement of the index finger
            cv2.polylines(img, [self.index_movement], False, (28, 49, 235), 15, 0) 

            self.curFrame = time.time() 
            self.delta_time = self.curFrame - self.prevFrame 

            # display score metrics
            cv2.putText(img, "Score: " + str(self.score), (int(w * 0.1), 60), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1.2, (181, 250, 87), 2)
            cv2.putText(img, "Level: " + str(self.difficulty_level), (int(w * 0.85), 60), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1.2, (181, 250, 87), 2)
            cv2.putText(img, "Lives: " + str(self.lives), (int(w * 0.5), 30), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1.2, (118, 62, 250), 2)

            self.prevFrame = self.curFrame

            if self.game_over:
                cv2.putText(img, "GAME OVER", (int(w * 0.35), int(h * 0.6)), cv2.FONT_HERSHEY_SIMPLEX, 3, (28, 49, 235), 6)
                self.geese.clear()
            else: 
                if (time.time() > self.next_goose_time):
                    self.create_goose() 
                    self.next_goose_time = time.time() + 1/self.goose_rate

                self.move_geese(img)

            cv2.imshow(self.title, img)
            
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break
            
        cap.release()
        cv2.destroyAllWindows()
    
    