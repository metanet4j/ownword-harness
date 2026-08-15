import type {ReactElement, ReactNode} from 'react';

export interface CardProps {
  children?: ReactNode;
  isSelected?: boolean;
  isQuiet?: boolean;
  onPress?: () => void;
}

export declare function Card(props: CardProps): ReactElement;
