import json
import os
from enum import Enum
from typing import TYPE_CHECKING, List, Type

import google.generativeai as genai
from dotenv import load_dotenv
from typing_extensions import TypedDict

from src.events import Event, EventType
from src.game_types import Message, Party, Policy, Role, Selection
from src.players.base import POLICY_MAPPING, VOTE_MAPPING, Player

if TYPE_CHECKING:
    from src.game_state import GameState

load_dotenv()
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")


BASE_PROMPT = """
# SECRET HITLER
## Game introduction:
At the beginning of the game, each player
is secretly assigned to one of three roles:
Liberal, Fascist, or Hitler. The Liberals have
a majority, but they don't know for sure who
anyone is; Fascists must resort to secrecy and
sabotage to accomplish their goals. Hitler plays
for the Fascist team, and the Fascists know
Hitler's identity from the outset, but Hitler
doesn't know the Fascists and must work to
figure them out.

The Liberals win by enacting five Liberal
Policies or killing Hitler. The Fascists win by
enacting six Fascist Policies, or if Hitler is
elected Chancellor after three Fascist Policies
have been enacted.

Whenever a Fascist Policy is enacted, the
government becomes more powerful, and the
President is granted a single-use power which
must be used before the next round can begin. It
doesn't matter what team the President is on; in
fact, even Liberal players might be tempted to
enact a Fascist Policy to gain new powers. 

## Game strategy notes:
 - Everyone should claim to be a Liberal. Since
the Liberal team has a voting majority, it can
easily shut out any player claiming to be a
Fascist. As a Fascist, there is no advantage to
outing yourself to the majority. Additionally,
Liberals should usually tell the truth. Liberals
are trying to figure out the game like a puzzle,
so lying can put their team at a
significant disadvantage.

 - If this is your first time playing Hitler,
just remember: be as Liberal as possible. Enact
Liberal Policies. Vote for Liberal governments.
Kiss babies. Trust your fellow Fascists to
create opportunities for you to enact Liberal
Policies and to advance Fascism on their turns.
The Fascists win by subtly manipulating the
table and waiting for the right cover to enact
Fascist Policies, not by overtly playing
as evil.

 - Liberals frequently benefit from slowing play
down and discussing the available information.
Fascists frequently benefit from rushing votes
and creating confusion.

 - Fascists most often win by electing Hitler,
not by enacting six Policies! Electing Hitler
isn't an optional or secondary win condition,
it's the core of a successful Fascist strategy.
Hitler should always play as a Liberal, and
should generally avoid lying or getting into
fights and disagreements with other players.
When the time comes, Hitler needs the Liberals'
trust to get elected. Even if Hitler isn't
ultimately elected, the distrust sown among
Liberals is key to getting Fascists elected late
in the game.

 - Ask other players to explain why they took
an action. This is especially important with
Presidential Powers—in fact, ask ahead of time
whom a candidate is thinking of investigating/
appointing/assassinating.

 - If a Fascist Policy comes up, there are only
three possible culprits: The President, the
Chancellor, or the Policy Deck. Try to figure
out who (or what!) put you in this position.
"""


def create_choice_prompt(
    title_message: str, input_message: str, choices: List[Player | Policy]
) -> str:
    messages = []
    messages.append(title_message)
    for i, choice in enumerate(choices, start=1):
        messages.append(f"\t{i} - {choice}")
    messages.append(f"\n{input_message}")
    return "\n".join(messages)


class Vote(Enum):
    y = "Y"
    n = "N"


class VoteDecision(TypedDict):
    thoughts: str
    selection: Vote


class Discussion(TypedDict):
    internal_thoughts: str
    public_chat: str


def create_enum_class(name: str, choices: List[Player]) -> Type[Enum]:
    return Enum(name, {f"Option{i+1}": str(i + 1) for i in range(len(choices))})


def create_schema(name: str, choices) -> Type[TypedDict]:
    selection = create_enum_class("selection", choices)
    return TypedDict(
        name,
        {
            "thoughts": str,
            "selection": selection,
        },
    )


class GeminiPlayer(Player):
    def build_game_log(self, game_state: "GameState", max_events: int = 150) -> str:
        events = game_state.event_history
        events.extend(game_state.public_chat)
        events.extend(self.thoughts)
        events = sorted(events, key=lambda x: x.time)

        logs = {"old": "", "new": ""}
        for event in events[-max_events:]:
            log = "old" if event.time <= self.last_logged_message_dt else "new"
            if isinstance(event, Message):
                chat_type = "INTERNAL THOUGHT" if event.internal else "PUBLIC CHAT"
                if event.author == self:
                    string = f"\n[{chat_type}][Myself]: {event.content}"
                else:
                    string = f"\n[{chat_type}][{event.author}]: {event.content}"

            else:
                string += f"\n[EVENT]: {event.description()}"

            logs[log] += string

        if events:
            self.last_logged_message_dt = events[-1].time

        event_log = ""
        if not (log["new"] or log["old"]):
            event_log += "\n## GAME EVENT HISTORY:\nThe game has just begun!\n"

        if log["old"]:
            event_log += f"\n## GAME EVENTS PRIOR TO LAST TURN:\n{log["old"]}\n"

        if log["new"]:
            event_log += f"\n## GAME EVENTS SINCE LAST TURN:\n{log["new"]}\n"

        return log

    def build_prompt(
        self, game_state: "GameState", choice_prompt: str, government_role: str = None
    ) -> str:
        prompt = BASE_PROMPT
        prompt += self.build_game_log(game_state)

        prompt += "\n## PLAYER INFO:"
        prompt += f"\nYour name: {self.name}"
        prompt += f"\nYour secret role: {self.role}"
        if government_role:
            prompt += f"\nYour current government position: {government_role}"

        allies = ""
        if self.party == Party.fascist:
            fascists = [x for x in game_state.players if x.party == Party.fascist and x != self]
            if self.role != Role.hitler or len(fascists) == 1:
                allies = "Your fascist allies:"
                for player in fascists:
                    allies += f"\t - {player.name}"

        prompt += allies
        prompt += f"\n\n## PROMPT:\n{choice_prompt}"

        return prompt

    def nominate_chancellor(self, game_state: "GameState", players: List[Player]) -> Player:
        choice_prompt = create_choice_prompt(
            title_message=f"{self.name}, you are the president and you must now nominate a chancellor:",
            input_message="Please nominate one of the above players as chancellor.",
            choices=players,
        )

        prompt = self.build_prompt(game_state, choice_prompt, government_role="President")

        Decision = create_schema("Decision", players)
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json", response_schema=Decision
            ),
        )

        data = json.loads(response.candidates[0].content.parts[0].text)
        choice_idx = int(data["selection"]) - 1
        thoughts = data.get("thoughts", "")

        chosen_player = players[choice_idx]
        game_state.event_history.append(
            Event(event_type=EventType.chancellor_nominated, actor=self, recipient=chosen_player)
        )
        self.thoughts.append(Message(author=self, internal=True, content=thoughts))

        print(f"Nominating {chosen_player}")

        return chosen_player

    def vote_on_government(
        self, game_state: "GameState", president: Player, chancellor: Player
    ) -> bool:
        choice_prompt = f"f\n{self.name} - Vote on government (president: {president.name}, chancellor: {chancellor.name}) [y/n]? "
        prompt = self.build_prompt(game_state, choice_prompt)

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json", response_schema=VoteDecision
            ),
        )

        data = json.loads(response.candidates[0].content.parts[0].text)
        vote_result = data["selection"].lower() == "y"
        thoughts = data.get("thoughts", "")

        game_state.event_history.append(Event(event_type=VOTE_MAPPING[vote_result], actor=self))
        self.thoughts.append(Message(author=self, internal=True, content=thoughts))

        return vote_result

    def propose_policies(self, game_state: "GameState", policy_cards: List[Policy]) -> Selection:
        choice_prompt = create_choice_prompt(
            title_message=f"{self.name} - Choose policies to discard (you must discard one):",
            input_message="Which policy to discard (1-3)?",
            choices=policy_cards,
        )

        prompt = self.build_prompt(game_state, choice_prompt, government_role="President")

        Decision = create_schema("ProposePoliciesDecision", policy_cards)
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json", response_schema=Decision
            ),
        )

        data = json.loads(response.candidates[0].content.parts[0].text)
        discard_idx = int(data["selection"]) - 1
        thoughts = data.get("thoughts", "")

        discarded = [policy_cards.pop(discard_idx)]
        self.thoughts.append(Message(author=self, internal=True, content=thoughts))

        return Selection(selected=policy_cards, discarded=discarded)

    def enact_policy(self, game_state: "GameState", policy_cards: List[Policy]) -> Policy:
        choice_prompt = create_choice_prompt(
            title_message=f"{self.name} - Choose a policy to enact:",
            input_message="Which policy to enact (1-2)?",
            choices=policy_cards,
        )

        prompt = self.build_prompt(game_state, choice_prompt, government_role="President")

        Decision = create_schema("EnactPolicyDecision", policy_cards)
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json", response_schema=Decision
            ),
        )

        data = json.loads(response.candidates[0].content.parts[0].text)
        enact_idx = int(data["selection"]) - 1
        thoughts = data.get("thoughts", "")

        selected = [policy_cards.pop(enact_idx)]
        game_state.event_history.append(Event(event_type=POLICY_MAPPING[selected[0]], actor=self))
        self.thoughts.append(Message(author=self, internal=True, content=thoughts))

        return Selection(selected=selected, discarded=policy_cards)

    def action_investigate_loyalty(self, game_state: "GameState", players: List[Player]):
        choice_prompt = create_choice_prompt(
            title_message=f"{self.name}, you are the president and you must now choose a player to investigate:",
            input_message="Which player would you like to check the party loyalty of?",
            choices=players,
        )

        prompt = self.build_prompt(game_state, choice_prompt, government_role="President")

        Decision = create_schema("Decision", players)
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json", response_schema=Decision
            ),
        )

        data = json.loads(response.candidates[0].content.parts[0].text)
        choice_idx = int(data["selection"]) - 1
        thoughts = data.get("thoughts", "")

        player = players[choice_idx]
        game_state.event_history.append(
            Event(event_type=EventType.loyalty_investigated, actor=self, recipient=player)
        )
        self.thoughts.append(Message(author=self, internal=True, content=thoughts))

        investigation = f"I have investigated the party loyalty of {player.name}, and I know with certainty that they are {player.role},"

        if player.party == self.party:
            investigation += " this means that we are on the same party."
        else:
            investigation += " this means that we are enemies."

        self.thoughts.append(Message(author=self, internal=True, content=investigation))

    def action_execution(self, game_state: "GameState", players: List[Player]) -> Player:
        choice_prompt = create_choice_prompt(
            title_message=f"{self.name}, you are the President and you must now choose a person in the game to execute:",
            input_message="Please nominate one of the above players.",
            choices=players,
        )

        prompt = self.build_prompt(game_state, choice_prompt, government_role="President")

        Decision = create_schema("Decision", players)
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json", response_schema=Decision
            ),
        )

        data = json.loads(response.candidates[0].content.parts[0].text)
        choice_idx = int(data["selection"]) - 1
        thoughts = data.get("thoughts", "")

        chosen_player = players[choice_idx]
        game_state.event_history.append(
            Event(event_type=EventType.chancellor_nominated, actor=self, recipient=chosen_player)
        )
        self.thoughts.append(Message(author=self, internal=True, content=thoughts))

        print(f"Nominating {chosen_player}")

        return chosen_player

    def action_policy_peek(self, game_state: "GameState", policy_cards: List[Policy]) -> None:
        game_state.event_history.append(Event(event_type=EventType.policy_peek, actor=self))

        cards = "\n".join(
            [f"{idx} - {card}" for idx, card in enumerate(policy_cards[-3:], start=1)]
        )
        thought = "I have reviewed the next 3 policies in secret, and I know with 100% confidence that the next 3 policies are:"
        thought += cards

        self.thoughts.append(Message(author=self, internal=True, content=thought))

    def discuss(self, game_state) -> None:
        discussion_prompt = (
            "It is now time to discuss, you should consider any questions you might want to ask the others, or "
            "perhaps respond to others if you have been asked, or even just speak your mind, but be aware this will be publicly broadcast "
            "to all other players"
        )

        prompt = self.build_prompt(game_state, discussion_prompt, government_role="President")

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json", response_schema=Discussion
            ),
        )

        data = json.loads(response.candidates[0].content.parts[0].text)
        thoughts = data.get("thoughts", "")
        public_chat = data.get("public_chat", "")

        self.thoughts.append(Message(author=self, internal=True, content=thoughts))
        game_state.public_chat.append(Message(author=self, content=public_chat))
