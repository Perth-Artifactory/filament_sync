from processors import siddament
from pprint import pprint

processors = [siddament]

filaments = []

# iterate over processors
for processor in processors:
    filaments += processor.all()
