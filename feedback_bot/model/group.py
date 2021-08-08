from dataclasses import dataclass


@dataclass
class Group:
    chat_id: int

    def __hash__(self):
        return hash(self.chat_id)
    
    def __eq__(self, other):
        return self.chat_id == other.chat_id
