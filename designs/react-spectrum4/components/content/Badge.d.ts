import type {ReactElement, ReactNode} from 'react';

export interface BadgeProps {
  children?: ReactNode;
  variant?: 'neutral' | 'accent' | 'informative' | 'positive' | 'negative' | 'notice';
}

export declare function Badge(props: BadgeProps): ReactElement;
