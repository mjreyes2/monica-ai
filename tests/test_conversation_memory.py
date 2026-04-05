"""Basic invariants & integrity tests for MonicaConversationMemory."""
import pytest

try:
    from monica_conversation_memory import MonicaConversationMemory
except ImportError:
    MonicaConversationMemory = None

pytestmark = pytest.mark.skipif(
    MonicaConversationMemory is None,
    reason="monica_conversation_memory module not available"
)

@pytest.fixture
def memory():
    """Create in-memory DB for fast tests."""
    return MonicaConversationMemory(db_path=":memory:")

def test_save_and_retrieve(memory):
    conv_id = memory.save_interaction(
        user_message="Hello Monica", monica_response="Hi there!", topic="Test"
    )
    recent = memory.get_recent_conversations(limit=1)
    assert len(recent) == 1
    assert recent[0].conv_id == conv_id

def test_unfinished_story_cycle(memory):
    item_id = memory.save_unfinished_story(
        title="My Story", content="Beginning...", item_type="story"
    )
    items = memory.get_unfinished_items()
    assert any(i["item_id"] == item_id for i in items)
    # Mark completed and ensure it's gone from pending list
    memory.mark_completed(item_id)
    items_after = memory.get_unfinished_items()
    assert not any(i["item_id"] == item_id for i in items_after)

def test_stats_consistency(memory):
    # Initially zero stats
    stats0 = memory.get_conversation_stats()
    assert stats0["total_conversations"] == 0
    # Add data
    memory.save_interaction("msg", "resp")
    memory.save_unfinished_story("t", "c")
    stats = memory.get_conversation_stats()
    assert stats["total_conversations"] == 1
    assert stats["unfinished_items"] == 1
