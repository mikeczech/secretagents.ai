from unittest.mock import MagicMock
from pytest import fixture
import pytest

from codenames.game import (
    AlreadyJoinedException,
    Color,
    Condition,
    NotStartedGameState,
    Role,
    RoleOccupiedException,
    SQLiteGamePersister,
    SpyTurnGameState,
    StateException,
)
from utils import create_default_game, add_players


class TestNotStartedGameState:
    @fixture
    def persister(self, db_con):
        persister = SQLiteGamePersister(42, db_con)
        create_default_game(db_con)
        return persister

    @fixture
    def not_started_state(self, persister):
        return NotStartedGameState("mysessionid", False, persister)

    def test_invalid_invocations(self, not_started_state):
        # when / then
        with pytest.raises(StateException):
            not_started_state.guess(0)

        with pytest.raises(StateException):
            not_started_state.give_hint("myhint", 2)

        with pytest.raises(StateException):
            not_started_state.end_turn()

    def test_cannot_join_twice(self, not_started_state):
        # when / then
        with pytest.raises(AlreadyJoinedException):
            not_started_state.join(Color.RED, Role.PLAYER)
            not_started_state.join(Color.BLUE, Role.PLAYER)

    def test_cannot_join_already_occupied_role(self, not_started_state):
        # when / then
        with pytest.raises(RoleOccupiedException):
            not_started_state.join(Color.RED, Role.PLAYER)
            not_started_state.join(Color.RED, Role.PLAYER)

    def test_start_game_fails_if_any_role_is_still_open(self, not_started_state):
        # when / then
        with pytest.raises(StateException):
            not_started_state.start_game()

    def test_start_game_foo(self, db_con, not_started_state):
        # given
        add_players(db_con)

        # when
        pre_condition = not_started_state.get_info()["metadata"]["condition"]
        not_started_state.start_game()
        post_condition = not_started_state.get_info()["metadata"]["condition"]

        # then
        assert pre_condition == Condition.NOT_STARTED
        assert post_condition == Condition.BLUE_SPY

    def test_cannot_start_game_twice(self, db_con, not_started_state):
        # given
        add_players(db_con)

        # when / then
        with pytest.raises(StateException):
            not_started_state.start_game()
            not_started_state.start_game()


class TestSpyTurnGameState:
    @fixture
    def persister(self, db_con):
        persister = SQLiteGamePersister(42, db_con)
        create_default_game(db_con)
        return persister

    @fixture
    def blue_spy_turn_state(self, persister):
        return SpyTurnGameState("mysessionid", False, persister, Color.BLUE)

    @fixture
    def red_spy_turn_state(self, persister):
        return SpyTurnGameState("mysessionid", False, persister, Color.RED)

    def test_invalid_invocations(self, blue_spy_turn_state):
        # when / then
        with pytest.raises(StateException):
            blue_spy_turn_state.guess(0)

        with pytest.raises(StateException):
            blue_spy_turn_state.start_game()

        with pytest.raises(StateException):
            blue_spy_turn_state.join(Color.RED, Role.PLAYER)

        with pytest.raises(StateException):
            blue_spy_turn_state.end_turn()

    @pytest.mark.parametrize(
        "spy_turn_state, initial_condition, color, final_condition",
        [
            ("red_spy_turn_state", Condition.RED_SPY, Color.RED, Condition.RED_PLAYER),
            (
                "blue_spy_turn_state",
                Condition.BLUE_SPY,
                Color.BLUE,
                Condition.BLUE_PLAYER,
            ),
        ],
    )
    def test_give_hint(
        self, spy_turn_state, initial_condition, color, final_condition, request
    ):
        # given
        spy_turn_state = request.getfixturevalue(spy_turn_state)
        spy_turn_state.persister.push_condition(initial_condition)

        # when
        pre_condition = spy_turn_state.get_info()["metadata"]["condition"]
        spy_turn_state.give_hint("myhint", 2)

        post_game_info = spy_turn_state.get_info()
        post_condition = post_game_info["metadata"]["condition"]
        latest_hint = post_game_info["hints"][-1]

        # then
        assert pre_condition == initial_condition
        assert post_condition == final_condition
        assert latest_hint["word"] == "myhint"
        assert latest_hint["num"] == 2
        assert latest_hint["color"] == color
