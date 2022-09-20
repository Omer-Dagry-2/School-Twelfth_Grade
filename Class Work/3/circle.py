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


class Circle(Shape):
    def __init__(self, radios: Union[int, float], color: str = None):
        """ Initialize The Circle """
        super().__init__(color=color)
        self.radios = radios
        self.set_area(3.141592653589793 * (self.radios ** 2))
        self.set_perimeter(3.141592653589793 * 2 * self.radios)

    def set_radios(self, radios: Union[int, float]):
        """ Set New Radios For The Circle """
        self.radios = radios
        self.set_area(3.141592653589793 * (self.radios ** 2))
        self.set_perimeter(3.141592653589793 * 2 * self.radios)

    def get_radios(self) -> Union[int, float]:
        """ Get The Circle Radios """
        return self.radios
