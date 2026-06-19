"""Unit tests for CLI flag parsing — verify all flags produce correct AnimationConfig."""

from __future__ import annotations

import pytest

from git_story_animator.cli import _build_parser, _build_config
from git_story_animator.models import Speed, Style


class TestCountFlag:
    """T019: --count / -n flag."""

    def test_count_long_flag(self):
        parser = _build_parser()
        args = parser.parse_args(["--count", "20"])
        config = _build_config(args)
        assert config.count == 20

    def test_count_short_flag(self):
        parser = _build_parser()
        args = parser.parse_args(["-n", "5"])
        config = _build_config(args)
        assert config.count == 5

    def test_count_default(self):
        parser = _build_parser()
        args = parser.parse_args([])
        config = _build_config(args)
        assert config.count == 10


class TestSpeedFlag:
    """T019: --speed flag (slow/normal/fast)."""

    def test_speed_slow(self):
        parser = _build_parser()
        args = parser.parse_args(["--speed", "slow"])
        config = _build_config(args)
        assert config.speed == Speed.SLOW

    def test_speed_normal(self):
        parser = _build_parser()
        args = parser.parse_args(["--speed", "normal"])
        config = _build_config(args)
        assert config.speed == Speed.NORMAL

    def test_speed_fast(self):
        parser = _build_parser()
        args = parser.parse_args(["--speed", "fast"])
        config = _build_config(args)
        assert config.speed == Speed.FAST

    def test_speed_default(self):
        parser = _build_parser()
        args = parser.parse_args([])
        config = _build_config(args)
        assert config.speed == Speed.NORMAL


class TestStyleFlag:
    """T019: --style flag (default/compact)."""

    def test_style_default(self):
        parser = _build_parser()
        args = parser.parse_args(["--style", "default"])
        config = _build_config(args)
        assert config.style == Style.DEFAULT

    def test_style_compact(self):
        parser = _build_parser()
        args = parser.parse_args(["--style", "compact"])
        config = _build_config(args)
        assert config.style == Style.COMPACT

    def test_style_default_by_default(self):
        parser = _build_parser()
        args = parser.parse_args([])
        config = _build_config(args)
        assert config.style == Style.DEFAULT


class TestReverseFlag:
    """T019: --reverse flag."""

    def test_reverse_set(self):
        parser = _build_parser()
        args = parser.parse_args(["--reverse"])
        config = _build_config(args)
        assert config.reverse is True

    def test_reverse_not_set(self):
        parser = _build_parser()
        args = parser.parse_args([])
        config = _build_config(args)
        assert config.reverse is False


class TestJsonFlag:
    """T019: --json flag."""

    def test_json_set(self):
        parser = _build_parser()
        args = parser.parse_args(["--json"])
        config = _build_config(args)
        assert config.json_mode is True

    def test_json_not_set(self):
        parser = _build_parser()
        args = parser.parse_args([])
        config = _build_config(args)
        assert config.json_mode is False


class TestNoInteractiveFlag:
    """T019/T030: --no-interactive flag."""

    def test_no_interactive_set(self):
        parser = _build_parser()
        args = parser.parse_args(["--no-interactive"])
        config = _build_config(args)
        assert config.interactive is False

    def test_no_interactive_not_set(self):
        parser = _build_parser()
        args = parser.parse_args([])
        config = _build_config(args)
        assert config.interactive is True


class TestCombinedFlags:
    """T019: Multiple flags at once."""

    def test_all_customization_flags(self):
        parser = _build_parser()
        args = parser.parse_args([
            "--count", "5",
            "--speed", "fast",
            "--style", "compact",
            "--reverse",
        ])
        config = _build_config(args)
        assert config.count == 5
        assert config.speed == Speed.FAST
        assert config.style == Style.COMPACT
        assert config.reverse is True


class TestVersionFlag:
    """T034: --version flag returns 0 and prints version."""

    def test_version_parsed(self):
        parser = _build_parser()
        args = parser.parse_args(["--version"])
        assert args.version is True
