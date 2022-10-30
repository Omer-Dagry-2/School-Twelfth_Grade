"""
Author: Omer Dagry
Mail: omerdagry@gmail.com
Date: 14/09/2022 (day/month/year)
"""
import os
from typing import *
if "shape.py" in os.listdir():
    from shape import Shape
else:
    raise AssertionError("Missing File: shape.py")


class Rectangle(Shape):
    def __init__(self, width: Union[int, float], length: Union[int, float], color: str = None):
        """ Initialize The Rectangle """
        super().__init__(color=color)
        self.width = width
        self.length = length
        super().set_area(self.width * self.length)
        super().set_perimeter(self.width * 2 + self.length * 2)

    def set_area(self, area: Union[int, float]):
        """ Don't Allow To Only Change The Area """
        return

    def set_perimeter(self, perimeter: Union[int, float]):
        """ Don't Allow To Only Change The Perimeter """
        return

    def set_width(self, width: Union[int, float]):
        """ Set Rectangle Width """
        self.width = width
        super().set_area(self.width * self.length)
        super().set_perimeter(self.width * 2 + self.length * 2)

    def set_length(self, length: Union[int, float]):
        """ Set Rectangle Length """
        self.length = length
        super().set_area(self.width * self.length)
        super().set_perimeter(self.width * 2 + self.length * 2)

    def get_width(self) -> Union[int, float]:
        """ Get Rectangle Width """
        return self.width

    def get_length(self) -> Union[int, float]:
        """ Get Rectangle Length """
        return self.length

    def connect_to_square(self, square):
        """
        Creates A New Rectangle The Has The Same Area And Perimeter As The square + This Rectangle Area And Perimeter
        :type square: Square
        """
        total_area = self.area + square.get_perimeter()
        total_perimeter = self.perimeter + square.get_perimeter()
        length_options = super().solve_quadratic_equation(1, -total_perimeter / 2, total_area)
        if length_options:
            length = length_options[0]
            width = total_area / length
            return Rectangle(width=width, length=length)
        else:
            return None

    def connect_to_rectangle(self, rectangle):
        """
        Creates A New Rectangle The Has The Same Area And Perimeter As The rectangle + This Rectangle Area And Perimeter
        :type rectangle: Rectangle
        """
        total_area = self.area + rectangle.get_perimeter()
        total_perimeter = self.perimeter + rectangle.get_perimeter()
        length_options = super().solve_quadratic_equation(1, -total_perimeter / 2, total_area)
        if length_options:
            length = length_options[0]
            width = total_area / length
            return Rectangle(width=width, length=length)
        else:
            return None


_ = Rectangle(5, 4)
assert _.get_area() == 20
assert _.get_perimeter() == 18
assert _.get_width() == 5
assert _.get_length() == 4
del _
