#!/usr/bin/env python3

# if not __package__ and not hasattr(sys, 'frozen'):
#     import os.path
#     import sys
#     path = os.path.realpath(os.path.abspath(__file__))
#     sys.path.insert(0, os.path.dirname(os.path.dirname(path)))

if __name__ == '__main__':
    from pyease_grpc import main
    main()
