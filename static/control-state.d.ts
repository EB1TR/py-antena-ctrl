export const TOPICS: string[];
export function createConsumer(onState: (state: Record<string, unknown>) => void, onFreshness?: (fresh: boolean) => void): {
  receive(topic: string, payload: string): boolean;
  disconnect(): void;
  isFresh(): boolean;
};
