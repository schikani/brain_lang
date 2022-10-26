from jsonDB import jsonDB as DB
from json import loads
import os

COMMENT = "#"
LOAD = "load"
WR = "wr"
WREVENT = "wrevent"
PRINT = "print"
PIPE = "|"
SEMI  = ":"
END = "end"
LEFT = "<"
RIGHT = ">"

TOKENS = [LOAD, WR, WREVENT, PRINT, PIPE, COMMENT]

BASE_DB_DIR = "DB"
if BASE_DB_DIR not in os.listdir("."):
    os.mkdir(BASE_DB_DIR)

def mk_db_dir(db_name):
    if db_name not in os.listdir(BASE_DB_DIR):
        os.mkdir(BASE_DB_DIR+"/"+db_name)
    
    return db_name

class Store_Rows():
    def __init__(self, db_file):
        self.db_file = db_file
        self.db = DB(BASE_DB_DIR, ".row_counts")

    def update(self, num_row):
        self.db.write(self.db_file, num_row)
        self.db.flush()

    def get_rows(self):
        if not self.db.exists(self.db_file):
            self.db.write(self.db_file, 0)
            self.db.flush()
        return self.db.read(self.db_file)

class Tokens():

    tokens = []

    def __init__(self, brl_file):
        self.line_num = 0
        self.brl_file = brl_file
        self.openfileobject = open(self.brl_file, "r")
        self.current_cmd = ""
        self.db_list = {}
        self.blocks = {}
        self.block_list = []
        self.block = ""
        self.current_json_str = ""

    @staticmethod
    def get_brain_extension(block):
        return block + ".brain"


    def advance(self):
        for line in self.openfileobject:
            self.line_num += 1
            if len(line) > 0:
                token = line.split()
                if len(token) > 0:
                    token = token[0]
                else:
                    token = ""

                if line.startswith(COMMENT):
                    pass

                elif token == END:
                    self.current_cmd = END
                    self.blocks[self.block] = self.current_json_str
                    self.block = ""
                    self.current_json_str = ""

                elif line.startswith(PIPE):
                    self.current_cmd = PIPE
                    self.block_list.append(line[line.index(line[1]):-2])
                    self.block = line[line.index(line[1]):-2]

                elif token == WR:
                    self.current_cmd = WR
                    self.block = line[line.index(LEFT)+1:line.index(RIGHT)]

                elif token == WREVENT:
                    self.current_cmd = WREVENT
                    self.block = line[line.index(LEFT)+1:line.index(RIGHT)]

                elif token not in TOKENS:
                    self.current_cmd = ""
                    self.current_json_str += line

            yield

class BrainLang(Tokens):
    def __init__(self, brl_file):
        super().__init__(brl_file)
        self.db_file = BASE_DB_DIR + "/" + mk_db_dir(self.brl_file)
        self.execute()
        
    def get_structure(self, block, **kwargs):
        result = self.blocks[block]
        for k, v in kwargs.items():
            result = result.replace("{%s}" % k, str(v))
        return loads(result)

    def write_data(self, block, db, is_static, **kwargs):
        d = {}
        for k, v in self.get_structure(block, **kwargs).items():
            d[k] = v
        if not is_static:
            store_rows = Store_Rows(self.db_file+"/"+self.get_brain_extension(block))
            num_rows = store_rows.get_rows()
            db.write(num_rows, d)
            store_rows.update(num_rows + 1)
        else:
            db.write(0, d)

    def read_event_data(self, block, key):
        if block in self.block_list:
            return self.db_list[block].read(key)
        else:
            return None

    def read_static_data(self, block):
        db = DB(self.db_file, self.get_brain_extension(block))
        val = db.read(0)
        return val
            
    def execute(self):
        for line in self.advance():
            if self.current_cmd == WR:
                db = DB(self.db_file, self.get_brain_extension(self.block))
                self.write_data(self.block, db, is_static=True)
                db.flush()

            elif self.current_cmd == WREVENT:
                self.db_list[self.block] = DB(self.db_file, self.get_brain_extension(self.block))

    def fire_event(self, block, **kwargs):
        if block in self.block_list:
            self.write_data(block, self.db_list[block], is_static=False, **kwargs)
            self.db_list[block].flush()

        else:
            print("Unknown event name '{}'".format(block))
            


# ~~~~~~~~
# Usage
# ~~~~~~~~

# replace "test.brl" with your custom script
# ob = BrainLang("test.brl")  