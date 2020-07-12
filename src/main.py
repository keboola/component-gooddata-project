import sys
from gooddata.component import GoodDataProjectComponent

# Environment setup
sys.tracebacklimit = 3

if __name__ == '__main__':

    c = GoodDataProjectComponent()
    c.run()
