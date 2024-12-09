import json
import os
from enum import Enum
from typing import TYPE_CHECKING, List, Type

import google.generativeai as genai
from typing_extensions import TypedDict

from src.events import Event, EventType, events_str
from src.game_types import Message, Policy, Selection, message_str
from src.players.base import POLICY_MAPPING, VOTE_MAPPING, Player

if TYPE_CHECKING:
    from src.game_state import GameState


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


def str_append(base: str, new: str) -> str:
    return "\n".join([base, new])


def create_choice_prompt(
    title_message: str, input_message: str, choices: List[Player | Policy]
) -> str:
    messages = []
    messages.append(title_message)
    for i, choice in enumerate(choices, start=1):
        messages.append(f"\t{i} - {choice}")
    messages.append(f"\n{input_message}")
    return "\n".join(messages)


def build_openapi_schema(choices: List[Player | Policy]) -> dict:
    schema = {
        "type": "object",
        "properties": {
            "thoughts": {"type": "string"},
            "selection": {"type": "integer", "minimum": 1, "maximum": len(choices)},
        },
        "required": ["thoughts", "selection"],
    }
    return schema


def create_enum_class(name: str, choices: List[Player]) -> Type[Enum]:
    return Enum(name, {f"Option{i+1}": str(i + 1) for i in range(len(choices))})


def create_typed_dict_class(name: str, selection: Type[Enum]) -> Type[TypedDict]:
    return TypedDict(
        name,
        {
            "thoughts": str,
            "selection": selection,
        },
    )


class GeminiPlayer(Player):
    def build_prompt(
        self, event_history: str, chat_history: str, choice_prompt: str, government_role: str = None
    ) -> str:
        prompt = BASE_PROMPT
        if event_history:
            prompt += f"\n## GAME EVENT HISTORY:\n{event_history}\n"
        else:
            prompt += "\n## GAME EVENT HISTORY:\nThe game has just begun!\n"

        if chat_history:
            prompt += f"\n## CHAT HISTORY (INCLUDING YOUR INTERNAL THOUGHTS):\n{chat_history}\n"

        prompt += "\n## PLAYER INFO:"
        prompt += f"\nYour name: {self.name}"
        prompt += f"\nYour secret role: {self.role}"
        if government_role:
            prompt += f"\nYour current government position: {government_role}"

        prompt += f"\n\n## PROMPT:\n{choice_prompt}"

        return prompt

    def nominate_chancellor(self, game_state: "GameState", players: List[Player]) -> Player:
        event_history = events_str(game_state.event_history)
        chat_history = message_str(self, game_state.public_chat, self.thoughts)

        choice_prompt = create_choice_prompt(
            title_message=f"{self.name}, you are the president and you must now nominate a chancellor:",
            input_message="Please nominate one of the above players as chancellor.",
            choices=players,
        )

        prompt = self.build_prompt(
            event_history, chat_history, choice_prompt, government_role="President"
        )

        # Dynamically create Selection enum and Decision TypedDict
        Selection = create_enum_class("Selection", players)
        Decision = create_typed_dict_class("Decision", Selection)

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json", response_schema=Decision, candidate_count=1
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

        return chosen_player

    def vote_on_government(
        self, game_state: "GameState", president: Player, chancellor: Player
    ) -> bool:
        while True:
            vote = input(
                f"f\n{self.name} - Vote on government (president: {president.name}, chancellor: {chancellor.name}) [y/n]? "
            ).lower()
            if vote in ["y", "n"]:
                vote_result = vote == "y"
                game_state.event_history.append(
                    Event(event_type=VOTE_MAPPING[vote_result], actor=self)
                )
                return vote_result

            print("Please enter 'y' or 'n'")

    def propose_policies(self, game_state: "GameState", policy_cards: List[Policy]) -> Selection:
        pass
        choice_idx = self.create_choice_prompt(
            title_message=f"{self.name} - Choose policies to discard (you must discard one):",
            input_message="Which policy to discard (1-3)?",
            choices=policy_cards,
        )

        discarded = [policy_cards.pop(choice_idx)]
        return Selection(selected=policy_cards, discarded=discarded)

    def enact_policy(self, game_state: "GameState", policy_cards: List[Policy]) -> Policy:
        choice_idx = self.create_choice_prompt(
            title_message=f"{self.name} - Choose a policy to enact:",
            input_message="Which policy to discard (1-2)?",
            choices=policy_cards,
        )
        selected = [policy_cards.pop(choice_idx)]
        game_state.event_history.append(Event(event_type=POLICY_MAPPING[selected[0]], actor=self))

        return Selection(selected=selected, discarded=policy_cards)

    def action_investigate_loyalty(self, game_state: "GameState", players: List[Player]):
        choice_idx = self.create_choice_prompt(
            title_message=f"{self.name} - Choose a player to investigate:",
            input_message="Which player?",
            choices=players,
        )

        player = players[choice_idx]
        game_state.event_history.append(
            Event(event_type=EventType.loyalty_investigated, actor=self, recipient=player)
        )
        print(f"\n{player.name} is a {player.party}")

    def action_execution(self, game_state: "GameState", players: List[Player]) -> Player:
        choice_idx = self.create_choice_prompt(
            title_message=f"{self.name} - Choose a player to execute:",
            input_message="Which player?",
            choices=players,
        )

        player = players[choice_idx]
        game_state.event_history.append(
            Event(event_type=EventType.player_executed, actor=self, recipient=player)
        )
        print(f"\n{player.name} has been executed")
        return player

    def action_policy_peek(self, game_state: "GameState", policy_cards: List[Policy]) -> None:
        print("\nThe next 3 policies are:")
        for idx, card in enumerate(policy_cards[-3:], start=1):
            print(f"{idx} - {card}")

        game_state.event_history.append(Event(event_type=EventType.policy_peek, actor=self))

    def discuss(self, game_state):
        return super().discuss(game_state)
