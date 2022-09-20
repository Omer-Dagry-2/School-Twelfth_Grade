"""
Author: Omer Dagry
Mail: omerdagry@gmail.com
Date: 14/09/2022 (day/month/year)
"""
import os
from typing import *
if "rectangle.py" in os.listdir():
    from rectangle import Rectangle
else:
    raise AssertionError("Missing File: rectangle.py")


class Square(Rectangle):
    def __init__(self, rib_length: Union[int, float], color: str = None):
        """ Initialize The Square """
        super().__init__(color=color, width=rib_length, length=rib_length)
        self.rib_length = rib_length
        self.set_area(self.rib_length ** 2)
        self.set_perimeter(self.rib_length * 4)

    def set_length(self, length: Union[int, float]):
        """ Blocks From Changing Only The Square Rib Length """
        raise Exception("Can't Change A Square Length, You Can Change All The Ribs Length To Another Length.\n"
                        "To Change The Square Ribs Length Use set_rib_length")

    def set_width(self, width: Union[int, float]):
        """ Blocks From Changing Only The Square Rib Width """
        raise Exception("Can't Change A Square Width, You Can Change All The Ribs Length To Another Length.\n"
                        "To Change The Square Ribs Length Use set_rib_length")

    def set_rib_length(self, rib_length: Union[int, float]):
        """ Set The Square Rib Length """
        self.rib_length = rib_length
        # need to use super because I override set_width and set_length,
        # so it won't be possible to change only the width or only the length
        super().set_width(rib_length)
        super().set_length(rib_length)
        self.set_area(self.rib_length ** 2)
        self.set_perimeter(self.rib_length * 4)

    def get_rib_length(self) -> Union[int, float]:
        """ Get The Square Rib Length """
        return self.rib_length

    def connect_to_rectangle(self, rectangle):
        """
        Creates A New Rectangle The Has The Same Area And Perimeter As The rectangle + This Square Area And Perimeter
        :type rectangle: Square
        """
        total_area = self.area + rectangle.get_perimeter()
        total_perimeter = self.perimeter + rectangle.get_perimeter()
        length_options = super().solve_quadratic_equation(1, -total_perimeter / 2, total_area)
        if length_options:
            length = length_options[0]
            width = total_area / length
            if width != length:
                return Rectangle(width=width, length=length)
            else:
                return Square(width)
        else:
            return None

    def connect_to_square(self, square):
        """
        Creates A New Rectangle The Has The Same Area And Perimeter As The square + This Square Area And Perimeter
        :type square: Square
        """
        total_area = self.area + square.get_perimeter()
        total_perimeter = self.perimeter + square.get_perimeter()
        length_options = super().solve_quadratic_equation(1, -total_perimeter / 2, total_area)
        if length_options:
            length = length_options[0]
            width = total_area / length
            if width != length:
                return Rectangle(width=width, length=length)
            else:
                return Square(width)
        else:
            return None
