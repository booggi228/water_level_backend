from json import JSONEncoder
import json
import datetime
import re
import numpy as np
#from script import eopatch, mydic

def time_conv(time):
    new_time = np.array([d.strftime('%Y.%m.%d') for d in time])
    return new_time

def list_of_dicts(marks):
    keys = marks.keys()
    vals = zip(*[marks[k] for k in keys])
    result = [dict(zip(keys, v)) for v in vals]
    return result

class NumpyArrayEncoder(JSONEncoder):

    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, datetime):
            return obj.tolist()
        if isinstance(obj, integer):
            return obj.tolist()
        return JSONEncoder.default(self, obj)

# COVERAGE_convert = [y for x in mydic['COVERAGE'] for y in x]

# def CRS_transform(data):

#     crs_conv = re.sub('\D', '', str(data))
#     a = list(crs_conv)
#     #b = ''.join(str(x) for x in a)

#     c = a*(len(COVERAGE_convert)-1)
#     cc = [c[i:i+(len(COVERAGE_convert)-1)] for i in range(0, len(c), (len(COVERAGE_convert)-1))]
#     #ccc = ''.join(str(x) for x in cc)

#     save = [''.join(x) for x in cc]
#     #savee = map(int, save)
#     return save
