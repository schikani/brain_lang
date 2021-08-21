from ubrainDB import ubrainDB as DB
import json

COMMENT = "#"
WR = "wr"
WREVENT = "wrevent"
RD = "rd"
LSQUARE = "["
RSQUARE = "]"
SEMI = ":"

TOKENS = [WR, WREVENT, LSQUARE, RSQUARE]

class Store_Rows():
    def __init__(self, db_file):
        self.db_file = db_file
        self.db = DB("."+self.db_file)

    def update(self, num_row):
        self.db.write(self.db_file, num_row)

    def get_rows(self):
        if self.db.read(self.db_file) == "Invalid key!":
            self.db.write(self.db_file, 0)
        return self.db.read(self.db_file)

class Tokens():

    tokens = []

    def __init__(self, brl_file):
        self.line_num = 0
        self.brl_file = brl_file
        self.openfileobject = open(self.brl_file, "r")
        self.current_cmd = ""
        self.events = {}
        self.current_json_file = ""

    def advance(self):
        for line in self.openfileobject:
            self.line_num += 1
            words = line.split()
            if len(words) > 0:

                if words[0][0] == COMMENT:
                    pass

                elif words[0] == WR:
                    self.current_cmd = WR
                    if words[1].find(LSQUARE) != -1 and words[1].find(RSQUARE) != -1:
                        self.current_json_file = words[1][words[1].find(LSQUARE)+1:words[1].find(RSQUARE)]
                        self.current_json_file += ".json"
                            
                    else:
                        print("Invalid syntax at line: {}".format(self.line_num))

                elif words[0] == WREVENT:
                    self.current_cmd = WREVENT

                    if words[1].find(LSQUARE) != -1 and words[1].find(RSQUARE) != -1:
                        event_name = words[1][words[1].find(LSQUARE)+1:words[1].find(SEMI)]
                        json_file = words[1][words[1].find(SEMI)+1:words[1].find(RSQUARE)]
                        json_file += ".json"
                        self.events[event_name] = {"j_file": json_file  , "db": DB(json_file.replace("/", "_").replace(".json", ".brain"))}
                            
                    else:
                        print("Invalid syntax at line: {}".format(self.line_num))
                
                else:
                    print("Invalid token '{}'".format(words[0]))

                yield


class BrainLang(Tokens):
    def __init__(self, brl_file):
        super().__init__(brl_file)
        self.execute()
        
    def get_structure(self, j_file, **kwargs):
        result = ""
        with open(j_file, "r") as pfile:
                result = pfile.read()
        for k, v in kwargs.items():
            result = result.replace("{%s}" % k, str(v))

        return json.loads(result)

    def write_data(self, j_file, db, **kwargs):
        d = {}
        for k, v in self.get_structure(j_file, **kwargs).items():
            d[k] = v
        store_rows = Store_Rows(j_file.replace("/", "_").replace(".json", ".brain"))
        num_rows = store_rows.get_rows()
        db.write(num_rows, d)
        store_rows.update(num_rows + 1)

    def read_event_data(self, event_name, key):
        if event_name in self.events.keys():
            return self.events[event_name]["db"].read(key)
        else:
            return None

    def read_static_data(self, db_file, key):
        db_file = db_file.replace("/", "_") + ".brain"
        store_rows = Store_Rows(db_file)
        db = DB(db_file)
        val = db.read(key)
        db.close()
        return val

            
    def execute(self):
        for line in self.advance():
            if self.current_cmd == WR:
                db = DB(self.current_json_file.replace("/", "_").replace(".json", ".brain"))
                self.write_data(self.current_json_file, db)
                db.close()

    def fire_event(self, event_name, **kwargs):
        if event_name in self.events.keys():
            self.write_data(self.events[event_name]["j_file"], self.events[event_name]["db"], **kwargs)

        else:
            print("Unknown event name '{}'".format(event_name))
            


# ~~~~~~~~
# Usage
# ~~~~~~~~

# replace "test.brl" with your custom script
# ob = BrainLang("test.brl")  