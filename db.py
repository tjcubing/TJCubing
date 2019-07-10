# Library for psuedo-database things

# class File:
#
#     def __init__(self):
#         pass
#
#     def __access__(value):
#         if value is None:
#             return load_file(self.file)
#         return load_file(self.file)[value]
#
#     def __modify__(key, value):
#         temp = self.__access__(None)
#         temp[key] = value
#         dump_file(temp, self.file)
