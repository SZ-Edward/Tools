#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Aurora Wu (wuxy91@gmail.com)'
__copyright__ = "Copyright (c) 2013 aurorawu.com"


def digit2wordin999(number):

    FIRST_TEN = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]

    SECOND_TEN = ["ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]

    OTHER_TENS = ["twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

    HUNDRED = "hundred"

    if number > 0:
        s = ''
        if 0 <= number <= 9:
            s = FIRST_TEN[number]   #0...9
        elif 10 <= number <= 99:
            if int(number / 10) == 1:
                s = SECOND_TEN[number%10]   #10...19
            elif number % 10 == 0 and number != 10:
                s = OTHER_TENS[int(number/10)-2]    #20/30/.../80/90
            else:
                s = OTHER_TENS[int(number/10)-2] + ' ' + FIRST_TEN[number%10]
        elif 100 <= number <= 999:
            if number % 100 == 0:
                s = FIRST_TEN[int(number/100)] + ' ' + HUNDRED   #100/200.../800/900
            elif number % 100 < 10:
                s = FIRST_TEN[int(number/100)] + ' ' + HUNDRED + ' ' + FIRST_TEN[number%10]  #X0X
            elif number % 100 < 20:
                s = FIRST_TEN[int(number/100)] + ' ' + HUNDRED + ' ' + SECOND_TEN[number%100-10] #X1X
            elif (number % 100) % 10 == 0:
                s = FIRST_TEN[int(number/100)] + ' ' + HUNDRED + ' ' + OTHER_TENS[int(number%100/10)-2] #XX0
            else:
                s = FIRST_TEN[int(number/100)] + ' ' + HUNDRED + ' ' + OTHER_TENS[int(number%100/10)-2] + ' ' + FIRST_TEN[number%100%10]   #XXX
        return s
    else:
        return 'Input a digit from 0 to 999, please!'