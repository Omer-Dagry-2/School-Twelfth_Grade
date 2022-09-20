"""
Author: Omer Dagry
Mail: omerdagry@gmail.com
Date: 14/09/2022 (day/month/year)
"""
import os
if "container.py" in os.listdir():
    from container import Container
else:
    raise AssertionError("Missing File: container.py")


def main():
    my_container = Container()
    my_container.generate(100)
    print("total area:", my_container.sum_areas())
    print("total perimeter:", my_container.sum_perimeters())
    print("colors:", my_container.count_colors())


if __name__ == '__main__':
    main()
