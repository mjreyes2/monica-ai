"""AI module for Monica AI - handles conversation and AI backends"""
from .conversation_manager import ConversationManager
from .knowledge_connector import KnowledgeConnector, get_knowledge_connector

__all__ = ['ConversationManager', 'KnowledgeConnector', 'get_knowledge_connector']
