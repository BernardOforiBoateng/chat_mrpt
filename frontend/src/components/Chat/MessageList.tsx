import React from 'react';
import type { Message } from '@/types';
import RegularMessage from './RegularMessage';
import ArenaMessage from './ArenaMessage';
import SystemMessage from './SystemMessage';
import ClarificationMessage from './ClarificationMessage';

interface MessageListProps {
  messages: Message[];
}

const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  return (
    <div className="space-y-4">
      {messages.map((message) => {
        switch (message.type) {
          case 'regular':
            return <RegularMessage key={message.id} message={message} />;
          case 'arena':
            return <ArenaMessage key={message.id} message={message} />;
          case 'system':
            return <SystemMessage key={message.id} message={message} />;
          case 'clarification':
            return <ClarificationMessage key={message.id} message={message} />;
          default:
            return null;
        }
      })}
    </div>
  );
};

export default MessageList;