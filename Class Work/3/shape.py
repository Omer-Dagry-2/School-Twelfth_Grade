"""
Author: Omer Dagry
Mail: omerdagry@gmail.com
Date: 14/09/2022 (day/month/year)
"""
import math
from typing import *


class Shape:
    def __init__(self, color: str = None, area: Union[int, float] = None, perimeter: Union[int, float] = None):
        """ Initialize The Shape """
        self.color = color
        self.area = area
        self.perimeter = perimeter

    def set_color(self, color: str):
        """ Set The Color Of The Shape """
        self.color = color

    def set_area(self, area: Union[int, float]):
        """ Set The Area Of The Shape """
        self.area = area

    def set_perimeter(self, perimeter: Union[int, float]):
        """ Set The Perimeter Of The Shape """
        self.perimeter = perimeter

    def get_color(self) -> str:
        """ Get The Color Of The Shape """
        return self.color

    def get_area(self) -> Union[int, float]:
        """ Get The Area Of The Shape """
        return self.area

    def get_perimeter(self) -> Union[int, float]:
        """ Get The Perimeter Of The Shape """
        return self.perimeter

    @staticmethod
    def solve_quadratic_equation(a: Union[int, float], b: Union[int, float], c: Union[int, float]) -> List[float]:
        """ Solves A Quadratic Equation And Returns A List With The Solution/s """
        options = []
        d = b ** 2 - 4 * a * c  # discriminant
        if d < 0:
            pass
        elif d == 0:
            x = (-b + math.sqrt(d)) / (2 * a)
            if x > 0:
                options.append(x)
        else:
            x1 = (-b + math.sqrt(d)) / (2 * a)
            if x1 > 0:
                options.append(x1)
            x2 = (-b - math.sqrt(d)) / (2 * a)
            if x2 > 0:
                options.append(x2)
        return options
