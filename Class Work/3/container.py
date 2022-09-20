"""
Author: Omer Dagry
Mail: omerdagry@gmail.com
Date: 14/09/2022 (day/month/year)
"""
import os
from typing import *
from random import randint
if "rectangle.py" and "square.py" and "circle.py" in os.listdir():
    from rectangle import Rectangle
    from square import Square
    from circle import Circle
else:
    raise AssertionError("Missing Files: " + ", ".join([missing_file for missing_file in
                                                        ["rectangle.py", "square.py", "circle.py"]
                                                        if missing_file not in os.listdir()]))


class Container:
    def __init__(self, min_length: Union[int, float] = 1, max_length: Union[int, float] = 20):
        """ Initialize The Container """
        self.items_list = []
        self.colors = ["Green", "Red", "Blue", "Orange", "Pink", "Yellow",
                       "Violet", "Brown", "Purple", "Gray", "White", "Black",
                       "Gold", "Silver", "Cyan"]
        self.min_length = min_length
        self.max_length = max_length

    def get_items_list(self) -> List:
        """ Get The Container Item List """
        return self.items_list

    def generate(self, number_of_items: int):
        """ Generate number_of_items Items And Appends To The Container items_list"""
        for i in range(0, number_of_items):
            rand = randint(0, 2)
            if rand == 0:  # rectangle
                color = self.colors[randint(0, len(self.colors) - 1)]
                shape = Rectangle(randint(self.min_length, self.max_length),
                                  randint(self.min_length, self.max_length))
                shape.set_color(color)
            elif rand == 1:  # square
                color = self.colors[randint(0, len(self.colors) - 1)]
                shape = Square(randint(self.min_length, self.max_length))
                shape.set_color(color)
            else:  # circle
                color = self.colors[randint(0, len(self.colors) - 1)]
                shape = Circle(randint(self.min_length, self.max_length))
                shape.set_color(color)
            self.items_list.append(shape)

    def sum_areas(self) -> Union[int, float]:
        """ Sums The Areas Of All The Items In The Container items_list """
        total_area = 0
        for shape in self.items_list:
            total_area += shape.get_area()
        return total_area

    def sum_perimeters(self) -> Union[int, float]:
        """ Sums The Perimeter Of All The Items In The Container items_list """
        total_perimeter = 0
        for shap in self.items_list:
            total_perimeter += shap.get_perimeter()
        return total_perimeter

    def count_colors(self) -> Dict:
        """ Sums The Number Of Times Each Color Appears In The Container items_list """
        colors_dict = {}
        for shape in self.items_list:
            if shape.get_color() in colors_dict:
                colors_dict[shape.get_color()] = colors_dict[shape.get_color()] + 1
            else:
                colors_dict[shape.get_color()] = 1
        return colors_dict
