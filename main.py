from kivy.app import App
from kivy.lang import Builder
from kivy.uix.image import Image
from kivy.animation import Animation
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.screenmanager import FadeTransition,  WipeTransition, SlideTransition
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.uix.textinput import TextInput
from kivy.uix.slider import Slider
from kivy.uix.carousel import Carousel
from kivy.core.text import LabelBase
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.stencilview import StencilView


import os
import numpy as np
import csv
import sqlite3

# DELETE AFTER TESTING----------------------------------------------------------->
os.environ['KIVY_METRICS_DPI'] = '96'
os.environ['KIVY_METRICS_PPI'] = '96'
os.environ['KIVY_METRICS_SCREEN'] = '1' 
#-------------------------------------------------------------------------------->

font_path = r"D:\Steven\Desktop\Python App\Fonts\Aclonica.ttf"
LabelBase.register(name="Aclonica", fn_regular=font_path)
Window.size = (322,684)
Window.maximum_width, Window.maximum_height = (322, 684)
startup_val = 0

class EzHomeScreen(Screen):
    # Function print button...
    def print(self):
        self.print_stocktaking_values('matrix.db','liquors')
    
    # Function leave button...
    def leave(self):
        self. clear_stored_values_on_exit()
        App.get_running_app().stop()

    # Function to clear stored single bottle readings----------------------------------------------------------
    def clear_stored_values_on_exit(self):
        conn = sqlite3.connect('matrix.db')
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(liquors)")  # Get all column names
        columns = [column[1] for column in cursor.fetchall()]        
        # Prepare the SQL statement to update rows 32,33,34 setting all columns to NULL
        update_query = f"""
            UPDATE liquors SET {', '.join([f'{col} = NULL' for col in columns])} WHERE rowid IN (32, 33, 34)
        """
        cursor.execute(update_query)
        conn.commit()
        print("Cleared all values in rows 32,33,34.")
        conn.close()

    def print_stocktaking_values(self, db_name, table_name):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")  
        columns = [column[1] for column in cursor.fetchall()]
        print("Column Headers:")
        print(columns)
        cursor.execute(f"SELECT * FROM {table_name} WHERE rowid = 33")
        row_33 = cursor.fetchone()    
        cursor.execute(f"SELECT * FROM {table_name} WHERE rowid = 34")
        row_34 = cursor.fetchone()
        summed_values = {}
        print("\nSummed Values (Row 33 + Row 34):")
        if row_33 and row_34:
            for header, value_33, value_34 in zip(columns, row_33, row_34):
                # Convert values to float, treating None or non-numeric values as 0
                try:
                    value_33 = float(value_33) if value_33 is not None else 0
                except ValueError:
                    value_33 = 0  # If it's not a valid number, treat it as 0

                try:
                    value_34 = float(value_34) if value_34 is not None else 0
                except ValueError:
                    value_34 = 0  # If it's not a valid number, treat it as 0

                summed_value = value_33 + value_34
                summed_values[header] = summed_value
                print(f"{header}: {summed_value}")
        else:
            print("No data found in Row 33 or Row 34")
        conn.close()

class EzLaunchScreen(Screen):     
    image1 = StringProperty("") 
    overlay_height = NumericProperty(684)
    overlay_opacity = NumericProperty(0) 
    #ToT_label_text = StringProperty('0')    

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.max_height = 684
        img_path1 = r'D:\Steven\Desktop\Python App\Images\Carousel\\' 
        img_path2 = r'D:\Steven\Desktop\Python App\Images\CarouselF\\' 
        # Funtion get images into carousel from path...Bottom
        layout = FloatLayout()
        self.background_image = Image(source=r'Images\launchScreen.png')
        layout.add_widget(self.background_image)
        self.carousel_widget = Carousel(direction='right', size_hint=(None, None), size=(322, self.overlay_height))        
        # Load images into carousel from path...
        for img_file in os.listdir(img_path1):
            if img_file.endswith(('.png', '.jpg', '.jpeg')):                 
                if not self.image1:
                    self.image1 = img_file.split('.')[0].upper()                  
                img = Image(source=os.path.join(img_path1, img_file), size_hint=(None, None), size=(322, self.overlay_height))
                self.carousel_widget.add_widget(img) 
        layout.add_widget(self.carousel_widget) 

        # Function to create an overlay container (StencilView to clip)
        self.overlay_container = StencilView(size_hint=(None, None), size=self.carousel_widget.size)
        self.overlay_container.pos = self.carousel_widget.pos  
        self.carouselF_widget = Carousel(direction='right', size_hint=(None, None), size=(322, self.overlay_height))   

        # Funtion get images into carouselF from path...Top
        for img_file in os.listdir(img_path2):
            if img_file.endswith(('.png', '.jpg', '.jpeg')):                 
                if not self.image1:
                    self.image1 = img_file.split('.')[0].upper()
                img = Image(source=os.path.join(img_path2, img_file), size_hint=(None, None), size=(322, self.overlay_height))
                self.carouselF_widget.add_widget(img)   

        self.overlay_container.add_widget(self.carouselF_widget)
        layout.add_widget(self.overlay_container)
        self.add_widget(layout)         

    # Function to clip overlay image to view underlay image to create liquid level variation...
    def update_overlay_height(self, value):
        slider = self.ids.slider_widget
        mapped_value = (value - slider.min) / (slider.max - slider.min)
        self.overlay_height = mapped_value * self.max_height
        if slider.value < 316.50:           
            self.overlay_container.height = slider.value - 15.5
        else:
            self.overlay_container.height = self.overlay_height    
        self.overlay_container.pos = (0, slider.y) 
    #..........................................................................................

    # Function to get initial values from sqlight db into slider......................
    def on_enter(self, *args):
        header_to_find = self.ids.brand_text.text.replace(" ", "_") 
        global startup_val
        startup_val = self.get_startup_val(header_to_find)
        if startup_val is not None:
            self.set_slider_value(startup_val)
            result = self.python_equivalent_of_excel_formula(startup_val, header_to_find)            
            if result is not None:
                self.ids.slider_tot.text = f"{result:.2f}"     
        self.get_value_from_row34(header_to_find)

        if 'slider_widget' in self.ids:
            # Bind the function to the process
            self.ids.slider_widget.bind(value=self.restrict_slider_value)
            self.ids.slider_widget.bind(value=self.update_result)

    #..............................................................

    # Function to get full - 30 tot - y value from sqlight database....................
    def get_startup_val(self, name):
        global startup_val, mx_val
        conn = sqlite3.connect('matrix.db')
        header_to_find = name.replace(" ", "_")
        cursor = conn.cursor()
        cursor.execute(f"SELECT {header_to_find} FROM liquors WHERE rowid = 32")
        row_32 = cursor.fetchone()
        if row_32 and row_32[0] is not None:
            startup_val = row_32[0] 
        else:
            cursor.execute(f'SELECT "{header_to_find}" FROM liquors LIMIT 1')
            row = cursor.fetchone()
            if row:
                startup_val = row[0]
                print(f"Value for {header_to_find} (row 1): {startup_val}")
            
        # Fetch the value from row 1 to store in mx_val for restricting the slider
        cursor.execute(f'SELECT "{header_to_find}" FROM liquors LIMIT 1') 
        row_1 = cursor.fetchone()
        if row_1 and row_1[0] is not None:
            mx_val = row_1[0] 
        conn.close()
        return startup_val 

    # Function to move between carousel images........
    def right_btn(self, *args):
        global startup_val
        self.carouselF_widget.load_next()
        self.carousel_widget.load_next()
        if self.carousel_widget.next_slide:  
            next_image_source = self.carousel_widget.next_slide.source
            next_image_name = next_image_source.split('\\')[-1].split('.')[0] 
            self.ids.brand_text.text = next_image_name.upper() 
            header_to_find = self.ids.brand_text.text.replace(" ", "_")
            self.first_value = self.get_startup_val(header_to_find)            
            startup_val = self.first_value
            self.update_slider_value(header_to_find)
            self.val_text.text = '0'
            self.get_value_from_row34(header_to_find)
           

    def left_btn(self, *args):
        global startup_val
        self.carouselF_widget.load_previous()
        self.carousel_widget.load_previous()
        if self.carousel_widget.previous_slide:
            prev_image_source = self.carousel_widget.previous_slide.source
            prev_image_name = prev_image_source.split('\\')[-1].split('.')[0] 
            self.ids.brand_text.text = prev_image_name.upper()
            header_to_find = self.ids.brand_text.text.replace(" ", "_")
            self.first_value= self.get_startup_val(header_to_find)        
            startup_val = self.first_value
            self.update_slider_value(header_to_find)
            self.val_text.text = '0'
            self.get_value_from_row34(header_to_find)
    #......................................... 
    
    # Function to update main slider value - (30 tot measurement position) - based on db extraction...
    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        
    def update_slider_value(self, dt):
        global startup_val
        if 'slider_widget' in self.ids:
            slider = self.ids.slider_widget
            slider.bind(value=self.restrict_slider_value)
            self.ids.slider_widget.bind(value=self.update_result)
            if startup_val is not None:
                slider.value = float(startup_val)

    def set_slider_value(self, new_value):
        if 'slider_widget' in self.ids:
            new_value = str(new_value) 
            print (f"new value is '{new_value}'")
            self.ids.slider_widget.value = new_value

    def restrict_slider_value(self, instance, value):
        global mx_val
        if mx_val is not None:
            max_allowed = float(mx_val)  
            if value > max_allowed:
                instance.value = max_allowed 
                return max_allowed
            print(f"Slider restricted to: {max_allowed}")
        else:
            print("mx_val is None, no restriction applied.")
            return value
        # End of slider value update code................................
    #Latest snippets 25/03/2025
    # Functions to get tot mapping...
    def get_tots(self, prod):
        conn = sqlite3.connect('matrix.db')
        cursor = conn.cursor()
        header_to_find = prod.replace(" ", "_")  # Ensure column names match
        cursor.execute(f'SELECT COUNT(*) FROM liquors')
        total_rows = cursor.fetchone()[0]
        cursor.execute(f'SELECT "{header_to_find}" FROM liquors LIMIT {total_rows - 3}')
        rows = cursor.fetchall()
        values = [float(row[0]) for row in rows if row[0] is not None]
        conn.close()
        return sorted(values)  # Ensure the values are sorted

    # Function to find the two closest values from the database based on slider value
    def find_closest_values(self, slider_value, c_values):
        for i in range(1, len(c_values)):
            if slider_value <= c_values[i]:
                return c_values[i-1], c_values[i], i-1, i
        return c_values[-2], c_values[-1], len(c_values)-2, len(c_values)-1

    # Function to map the slider value to the range [30, 0] based on interpolation
    def map_slider_to_range(self, slider_value, c_values):
        """
        Maps the slider value to a range from 30 to 0 based on its closest value in the c_values list.
        """
        lower_value, upper_value, lower_index, upper_index = self.find_closest_values(slider_value, c_values)
        
        # Linear interpolation
        proportion = (slider_value - lower_value) / (upper_value - lower_value)
        mapped_index = lower_index + proportion * (upper_index - lower_index)
        
        # Map the index to the range [0, 30]
        y_min = 0  # The minimum value for the target range
        y_max = 30  # The maximum value for the target range
        mapped_value = (mapped_index / (len(c_values) - 1)) * y_max
        
        # Round the result to nearest 0.25
        mapped_value = round(mapped_value * 4) / 4  
        mapped_value = max(min(mapped_value, 30), 0)  # Clamp between 0 and 30
        
        return float(mapped_value)

    def python_equivalent_of_excel_formula(self, slider_value, prod):
        slider_value = float(slider_value)
        c_values = self.get_tots(prod)
        
        # Check if the slider value is within bounds
        if slider_value < min(c_values) or slider_value > max(c_values):
            print(f"Slider value {slider_value} is out of bounds.")
            return None
        
        mapped_value = self.map_slider_to_range(slider_value, c_values)
        print(f"Mapped value is '{mapped_value}'")
    
        return float(mapped_value)

    def update_result(self, instance, value):
        slider_value = value        
        header_to_find = self.ids.brand_text.text.replace(" ", "_")        
        # Use the python_equivalent_of_excel_formula method to calculate the result
        result = self.python_equivalent_of_excel_formula(slider_value, header_to_find)        
        if result is not None:
            self.ids.slider_tot.text = f"{result:.2f}"        
        self.add_value_to_row32(header_to_find, slider_value)
        self.add_value_to_row33(header_to_find, self.tot_text.text) 
    
    #...............................................................................

    # This function passes the slider value to row 32 to be called later    
    def add_value_to_row32(self, prod, value):
        global mx_val  # To get the max allowed value
        if mx_val is not None:
            max_allowed = float(mx_val)
            value = min(value, max_allowed)
        conn = sqlite3.connect('matrix.db')
        prod = prod.replace(" ", "_")  # Replace spaces with underscores in the column name
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info(liquors)")  # Get the column names
        columns = [column[1] for column in cursor.fetchall()]
        if prod not in columns:
            print(f"Column '{prod}' does not exist.")
            conn.close()
            return        
        # Check if row 32 exists
        cursor.execute(f"SELECT {prod} FROM liquors WHERE rowid = 32")
        row = cursor.fetchone()
        if row and row[0] is not None:
            # If row 32 already has a value, overwrite it with the new value
            cursor.execute(f"UPDATE liquors SET {prod} = ? WHERE rowid = 32", (value,))
            print(f"Value in row 32 for column '{prod}' was overwritten with '{value}'.")
        else:
            # If row 32 doesn't have a value (i.e., it's NULL), just update it
            cursor.execute(f"UPDATE liquors SET {prod} = ? WHERE rowid = 32", (value,))
            print(f"Value '{value}' added (overwritten) in row 32 for column '{prod}'.")
        conn.commit()
        conn.close()

    # This function passes the tot reading to row 33
    def add_value_to_row33(self, prod, value):       
        value = str(value)
        conn = sqlite3.connect('matrix.db')
        prod = prod.replace(" ", "_")  # Replace spaces with underscores in the column name
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info(liquors)")  # Get the column names
        columns = [column[1] for column in cursor.fetchall()]
        if prod not in columns:
            print(f"Column '{prod}' does not exist.")
            conn.close()
            return        
        # Check if row 33 exists
        cursor.execute(f"SELECT {prod} FROM liquors WHERE rowid = 33")
        row = cursor.fetchone()        
        if row and row[0] is not None:
            # If row 33 already has a value, overwrite it with the new value
            cursor.execute(f"UPDATE liquors SET {prod} = ? WHERE rowid = 33", (value,))
            print(f"Value in row 33 for column '{prod}' was overwritten with '{value}'.")
        else:
            # If row 33 doesn't have a value (i.e., it's NULL), just update it
            cursor.execute(f"UPDATE liquors SET {prod} = ? WHERE rowid = 33", (value,))
            print(f"Value '{value}' added (overwritten) in row 33 for column '{prod}'.")        
        conn.commit()
        conn.close()
        
    # This function passes the slider value to row 34 to be called later  
    def add_value_to_row34(self, prod, value):
        conn = sqlite3.connect('matrix.db')
        prod = prod.replace(" ", "_")  # Replace spaces with underscores in the column name
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info(liquors)")  # Get the column names
        columns = [column[1] for column in cursor.fetchall()]
        if prod not in columns:
            print(f"Column '{prod}' does not exist.")
            conn.close()
            return        
        # Check if row 34 exists
        cursor.execute(f"SELECT {prod} FROM liquors WHERE rowid = 34")
        row = cursor.fetchone()
        if row and row[0] is not None:
            # If row 34 already has a value, overwrite it with the new value
            cursor.execute(f"UPDATE liquors SET {prod} = ? WHERE rowid = 34", (value,))
            print(f"Value in row 33 for column '{prod}' was overwritten with '{value}'.")
        else:
            # If row 34 doesn't have a value (i.e., it's NULL), just update it
            cursor.execute(f"UPDATE liquors SET {prod} = ? WHERE rowid = 34", (value,))
            print(f"Value '{value}' added (overwritten) in row 34 for column '{prod}'.")
        conn.commit()
        conn.close()

    def get_value_from_row34(self, prod):
        conn = sqlite3.connect('matrix.db')
        prod = prod.replace(" ", "_")
        cursor = conn.cursor()        
        cursor.execute(f"SELECT {prod} FROM liquors WHERE rowid = 34")
        row_34 = cursor.fetchone()
        if row_34 and row_34[0] is not None:
            self.ids.ToT_label.text  = row_34[0]
        conn.close()




               
    # Function get slider values..............
    def slide_it(self, *args):
        self.slide_text.text = str(args[1])
    #.........................................
    
    # Function add full bottles...............
    def add_it(self, *args):
        X1 = int(self.val_text.text)
        X2 = 30 
        X3 = X1 + X2 
        self.val_text.text =str(X3)
        #self.val_text.text = str(int(X3))
        header_to_find = self.ids.brand_text.text.replace(" ", "_")
        self.add_value_to_row34(header_to_find, self.val_text.text)
    #.........................................
    
    # Function remove full bottles...
    def min_it(self, *args):
        X1 = int(self.val_text.text)
        X2 = 30 
        X3 = X1 - X2
        X3 = np.where(X3<0,0,X3)
        self.val_text.text = str(X3)
        #self.val_text.text = str(int(X3))
        header_to_find = self.ids.brand_text.text.replace(" ", "_")
        self.add_value_to_row34(header_to_find, self.val_text.text)

     # Code to record mouse touch point................................
    def on_touch_down(self, touch):
        """ Detects mouse click and prints the y-position without moving the slider """
        # Prevent touch events from affecting other widgets (like the slider)
        if self.collide_point(*touch.pos):  
            print(round(touch.y))
            #return True  # Comment this out if slider must not be effected

        return super().on_touch_down(touch)

    # This function allows for swipe action...
    #def on_touch_move(self, touch):
        # ThresHold = 0
        # # Check if the touch move is a swipe and determine the direction
        # if self.carouselF_widget.collide_point(touch.x, touch.y):
        #     if touch.dx > ThresHold: 
        #         self.carouselF_widget.load_next()
        #         self.carousel_widget.load_next() 
        #     elif touch.dx < ThresHold: 
        #         self.carouselF_widget.load_previous()
        #         self.carousel_widget.load_previous()  
        # return super().on_touch_move(touch)
    #.................................................................

sm = ScreenManager()
sm.add_widget(EzHomeScreen(name='EzHome'))
sm.add_widget(EzLaunchScreen(name='EzLaunch'))


Code = """
ScreenManager:
    EzHomeScreen:
    EzLaunchScreen:    

<EzHomeScreen>:
    name: 'EzHome'
    BoxLayout:
        orientation: 'vertical'
        canvas.before:
            Rectangle:
                pos: self.pos
                size: self.size
                source: 'Images\main.png'                     
    FloatLayout:           
        Button:
            background_color: 0, 0 ,0, 0
            size_hint: .32, .046         
            on_press: root.manager.current = 'EzLaunch'            
            pos_hint: {'center_x': 0.83, 'center_y': 0.165}   
            Image:
                source: 'Images\launch.png'
                center_x: self.parent.center_x
                center_y: self.parent.center_y
        Button:
            background_color: 0, 0 ,0, 0
            size_hint: .32, .046         
            on_press: root.leave() 
            pos_hint: {'center_x': 0.17, 'center_y': 0.165}   
            Image:
                source: 'Images\leave.png'
                center_x: self.parent.center_x
                center_y: self.parent.center_y
        Button:
            background_color: 0, 0 ,0, 0
            size_hint: .32, .046         
            on_press: root.print() 
            pos_hint: {'center_x': 0.498, 'center_y': 0.165}   
            Image:
                source: 'Images\print.png'
                center_x: self.parent.center_x
                center_y: self.parent.center_y     

<EzLaunchScreen>: 
    name: 'EzLaunch'

    val_text: ToT_label
    slide_text: slider_label 
    tot_text: slider_tot
    # This used to be position last...
    FloatLayout:      
        # This is the slider control for alcohol levels...         
        Slider:
            background_color: 0, 0, 0, 0
            background_width: 1
            id: slider_widget       
            min: 33
            max: 684
            step: 0.25
            value: 0
            cursor_image: 'Images\slider.png' 
            cursor_width: 236
            cursor_height: 15.05 
            orientation: 'vertical'
            size_hint: None, None
            size: '320dp', '684dp'
            pos_hint: {'x': 0,'y': 0.027} 
            on_value: root.slide_it(*args)
            on_value: root.update_overlay_height(self.value)  

    FloatLayout:
        # Code for right swipe...
        Button:
            id: right_btn
            background_color: 0, 0, 0, 0
            size_hint: .25, .070 
            on_press: root.right_btn()   
            pos_hint: {'center_x': 0.90, 'center_y': .975}
        # Code for left swipe            
        Button:
            id: left_btn
            background_color: 0, 0, 0, 0
            size_hint: .25, .070            
            on_press: root.left_btn() 
            pos_hint: {'center_x': 0.10, 'center_y': .975} 
        # Code for brand selection...
        Label: 
            markup: True  
            id: brand_text
            font_name:  'Fonts\Aclonica.ttf' 
            text: root.image1 
            font_size: 20
            background_color: (0, 0, 0, 1)
            size_hint: (.55, 0.056)
            pos_hint: {'center_x': 0.50, 'center_y': .971}  
            height: 40 
            canvas.before:
                Color:
                    rgba: self.background_color
                Rectangle:  
                    size: self.size
                    pos: self.pos
        # Code for remaining tots label...           
        Label:
            id: ToT_label                    
            text: '0'       
            color: 246/255, 190/255, 0/255
            font_name: 'Fonts\Aclonica.ttf'       
            font_size: 12
            background_color: (0, 0, 0, 1)
            size_hint: (.110, 0.044)
            pos_hint: {'center_x': 0.5, 'center_y': .899} 
            height: 40 
            canvas.before:
                Color:
                    rgba: self.background_color
                Rectangle:  
                    size: self.size
                    pos: self.pos
        # Code for slider label measurement
        Label:  
            id: slider_label             
            text: '0'
            color: 246/255, 190/255, 0/255  
            font_name: 'Fonts\Aclonica.ttf'     
            font_size: 17
            background_color: (0, 0, 0, 1)
            size_hint: (.25, 0.055)
            pos_hint: {'center_x': 0.50, 'center_y': .845}             
            height: 40 
            canvas.before:
                Color:
                    rgba: self.background_color
                Rectangle:  
                    size: self.size
                    pos: self.pos     

        # New label for calcs.................
        Label:  
            id: slider_tot        
            text: '0'
            color: 246/255, 190/255, 0/255  
            font_name: 'Fonts\Aclonica.ttf'     
            font_size: 17
            background_color: (0, 0, 0, 1)
            size_hint: (.25, 0.055)
            pos_hint: {'center_x': 0.50, 'center_y': .845}             
            height: 40 
            canvas.before:
                Color:
                    rgba: self.background_color
                Rectangle:  
                    size: self.size
                    pos: self.pos 
        # Code for Home button...
        Button:
            background_color: 0, 0, 0, 0
            size_hint: 1.2, .045         
            on_press: root.manager.current = 'EzHome' 
            pos_hint: {'center_x': 0.50, 'center_y': 0.022}        
        # Coding for plus|minus buttons...        
        Button:            
            background_color: 0, 0, 0, 0
            size_hint: .099, .044 
            on_press: root.add_it(*args)
            pos_hint: {'center_x': 0.795, 'center_y': .898}        
        Button:
            background_color: 0, 0, 0, 0
            size_hint: .099, .044 
            on_press: root.min_it(*args)
            pos_hint: {'center_x': 0.208, 'center_y': .8995}       
                
"""

class ToTSlider(App):
    def build(self):
        Window.left = 1675  # For display 1 on the right (1920px for a 1080p display)
        Window.top = 50  # Top of the screen
        scr = Builder.load_string(Code)
        return scr
    

if __name__ == '__main__':
    ToTSlider().run()