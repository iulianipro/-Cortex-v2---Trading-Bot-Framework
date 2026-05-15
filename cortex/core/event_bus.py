"""
Event Bus - Publisher-Subscriber pattern implementation
Decouples all components through event-driven architecture
"""

import asyncio
from typing import Callable, Any, Dict, List
from datetime import datetime
from dataclasses import dataclass, asdict
import json
from cortex.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Event:
    """Base event class"""
    event_type: str
    timestamp: datetime
    source: str
    data: Dict[str, Any]
    
    def to_dict(self):
        return {
            'event_type': self.event_type,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'data': self.data
        }


class EventBus:
    """
    Central event bus for inter-component communication.
    All components communicate asynchronously through this bus.
    """
    
    def __init__(self, max_queue_size: int = 1000):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_queue = asyncio.Queue(maxsize=max_queue_size)
        self._event_history: List[Event] = []
        self._max_history = 10000
        self._is_running = False
        
    async def subscribe(self, event_type: str, handler: Callable) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to listen for (e.g., "market_update", "signal_generated")
            handler: Async callable that processes the event
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        self._subscribers[event_type].append(handler)
        logger.info(f"Subscribed {handler.__name__} to {event_type}")
    
    async def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe from an event type"""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(handler)
            logger.info(f"Unsubscribed {handler.__name__} from {event_type}")
    
    async def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event: Event object to publish
        """
        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]
        
        # Log event
        logger.debug(f"Event published: {event.event_type} from {event.source}")
        
        # Enqueue for processing
        await self._event_queue.put(event)
    
    async def start(self) -> None:
        """Start the event processing loop"""
        self._is_running = True
        logger.info("Event Bus started")
        
        while self._is_running:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                
                # Get subscribers for this event type
                handlers = self._subscribers.get(event.event_type, [])
                
                if handlers:
                    # Execute all handlers concurrently
                    tasks = [self._safe_execute_handler(h, event) for h in handlers]
                    await asyncio.gather(*tasks, return_exceptions=True)
                else:
                    logger.warning(f"No subscribers for event type: {event.event_type}")
                
                self._event_queue.task_done()
            
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {str(e)}")
    
    async def stop(self) -> None:
        """Stop the event processing loop"""
        self._is_running = False
        logger.info("Event Bus stopped")
    
    @staticmethod
    async def _safe_execute_handler(handler: Callable, event: Event) -> None:
        """Execute handler with error handling"""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
        except Exception as e:
            logger.error(f"Handler {handler.__name__} failed: {str(e)}")
    
    def get_event_history(self, event_type: str = None, limit: int = 100) -> List[Dict]:
        """
        Retrieve event history for analysis/debugging.
        
        Args:
            event_type: Filter by event type (optional)
            limit: Maximum number of events to return
        
        Returns:
            List of event dictionaries
        """
        history = self._event_history
        
        if event_type:
            history = [e for e in history if e.event_type == event_type]
        
        return [e.to_dict() for e in history[-limit:]]


# Singleton instance
_event_bus: EventBus = None


def get_event_bus() -> EventBus:
    """Get or create the global event bus instance"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


async def emit_event(event_type: str, source: str, data: Dict[str, Any]) -> None:
    """
    Convenience function to emit an event.
    
    Usage:
        await emit_event("market_update", "binance_fetcher", {
            "symbol": "BTCUSDT",
            "price": 65000.0,
            "volume": 1200.5
        })
    """
    event = Event(
        event_type=event_type,
        timestamp=datetime.utcnow(),
        source=source,
        data=data
    )
    await get_event_bus().publish(event)
