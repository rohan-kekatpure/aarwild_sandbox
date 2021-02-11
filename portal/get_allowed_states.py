import json
from dataclasses import dataclass

@dataclass
class JobState(dict):
    code: int
    definition: str
    display_name: str
    type_: int
    jump: int
    rank: int

    def __setattr__(self, key, value):
        super().__setitem__(key, value)
        self.__dict__[key] = value    

def _get_state_table() -> dict:
    # In practice this table should be fetched via DB query
    #
    # qry = '''select code, definition, display_name,
    #                 type, jump, rank
    #          from enum_job_state;'
    # state_table = DBM.exec_qry(qry)

    state_table = \
        """
        code,definition,display_name,type,jump,rank
        1,SUBMITTED,New,0,1,100
        2,INPROC_SEGMENTATION,Segmentation In-Progress,0,0,150
        3,DONE_SEGMENTATION,Ready for part making,0,1,200
        4,INPROC_ASSEMBLY,Assembly In-Progress,0,0,350
        5,DONE_ASSEMBLY,Ready for Fine-tuning,0,1,400
        6,INPROC_FINETUNING,Fine-tuning In-Progress,0,0,450
        7,DONE_FINETUNING,Ready for Packaging,0,1,500
        8,INPROC_PACKAGING,Packaging In-Progress,0,0,550
        9,DONE_PACKAGING,Ready for admin approval,0,1,600
        10,INPROC_QA,Admin approval in progress,0,0,650
        11,DONE_QA,Ready for client review,1,0,700
        12,PARENTED,Job Linked,0,0,0
        15,CLIENT_REVIEW,Client Review In-Progress,1,0,750
        16,CLIENT_APPROVED,Client Approved,1,0,800
        17,CLIENT_REJECTED,Client Rejected,1,0,810
        18,QA_REJECTED,Admin Reject,0,0,710
        19,REDO,Sent for Redo,1,0,0
        20,CLOSED,Closed,0,0,0
        21,UPLOAD PENDING,Upload Pending QA,0,0,0
        22,INPROC_PARTMKG,Part making in progress,0,0,250
        23,DONE_PARTMKG,Ready for assembly,0,1,300
        1005,FAILED_ASSEMBLY,Assembly Failed,0,0,399
        1007,FAILED_FINETUNING,Assembly Fine-tuning,0,0,499
        1009,FAILED_PACKAGING,Packaging Failed,0,0,599
        1010,FAILED_PARTMKG,Part making failed,0,0,299
        """

    state_strings = [line.strip() for line in state_table.split('\n')]
    state_strings = state_strings[2:-1]
    state_dict = {}
    for state_str in state_strings:
        code, defn, dispname, type_, jump, rank = state_str.split(',')
        code = int(code)
        type_ = int(type_)
        jump = int(jump)
        rank = int(rank)
        state_dict[defn] = JobState(code, defn, dispname, type_, jump, rank)

    return state_dict

def _get_allowed_states(state_dict: dict, current_state_name: str) -> list:
    current_state = state_dict[current_state_name]
    allowed_states = []

    for state_name, state in state_dict.items():
        if (state.jump == 1) and (state.rank < current_state.rank):
            allowed_states.append(state)

    if current_state_name == 'DONE_PACKAGING':
        qa_states = [state_dict['DONE_QA'], state_dict['CLIENT_APPROVED']]
        allowed_states.extend(qa_states)

    return allowed_states

def get_state_transitions() -> dict:
    state_dict = _get_state_table()
    transitions = {}
    for state_name in state_dict:
        allowed = _get_allowed_states(state_dict, state_name)
        transitions[state_name] = allowed
    return transitions

if __name__ == '__main__':
    tx = get_state_transitions()
    with open('transitions.json', 'w') as f:
        json.dump(tx, f, indent=2)
