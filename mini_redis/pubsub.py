"""단일 프로세스 REPL용 채널 기반 Pub/Sub 브로커."""

from mini_redis.datastructures.doubly_linked_list import DoublyLinkedList
from mini_redis.datastructures.hash_map import HashMap


class Subscriber:
    """구독자 식별자와 수신 대기 메시지 버퍼를 저장한다."""

    def __init__(self, identifier: str):
        """빈 메시지 버퍼를 가진 구독자를 만든다."""
        self.identifier = identifier
        self.messages = DoublyLinkedList()


class Channel:
    """채널 이름과 구독자 해시맵을 저장한다."""

    def __init__(self, name: str):
        """빈 구독자 목록을 가진 채널을 만든다."""
        self.name = name
        self.subscribers = HashMap()


class PubSubBroker:
    """채널 구독과 구독자별 FIFO 메시지 버퍼를 관리한다."""

    def __init__(self):
        """빈 채널 저장소를 만든다."""
        self._channels = HashMap()

    def subscribe(self, channel_name: str, subscriber_id: str) -> bool:
        """구독자를 채널에 등록하고, 새 등록이면 True를 반환한다."""
        channel = self._channels.get(channel_name)
        if channel is None:
            channel = Channel(channel_name)
            self._channels.put(channel_name, channel)
        if channel.subscribers.contains(subscriber_id):
            return False
        channel.subscribers.put(subscriber_id, Subscriber(subscriber_id))
        return True

    def publish(self, channel_name: str, message: str) -> int:
        """채널의 모든 구독자 버퍼에 메시지를 넣고 수신자 수를 반환한다."""
        channel = self._channels.get(channel_name)
        if channel is None:
            return 0

        subscriber_ids = channel.subscribers.keys()
        index = 0
        while index < len(subscriber_ids):
            subscriber = channel.subscribers.get(subscriber_ids[index])
            subscriber.messages.insert_back(message)
            index += 1
        return len(subscriber_ids)

    def subscription_count(self, subscriber_id: str) -> int:
        """구독자가 등록된 채널 수를 반환한다."""
        channel_names = self._channels.keys()
        count = 0
        index = 0
        while index < len(channel_names):
            channel = self._channels.get(channel_names[index])
            if channel.subscribers.contains(subscriber_id):
                count += 1
            index += 1
        return count

    def drain_messages(self, channel_name: str, subscriber_id: str):
        """구독자 버퍼의 메시지를 FIFO 순서로 반환하고 비운다."""
        channel = self._channels.get(channel_name)
        if channel is None:
            return []
        subscriber = channel.subscribers.get(subscriber_id)
        if subscriber is None:
            return []

        messages = []
        message = subscriber.messages.remove_front()
        while message is not None:
            messages.append(message)
            message = subscriber.messages.remove_front()
        return messages
