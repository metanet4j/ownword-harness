import type {ReactElement, ReactNode} from 'react';

export interface InlineAlertProps {
  children?: ReactNode;
  heading?: string;
  variant?: 'neutral' | 'informative' | 'positive' | 'negative';
  fillStyle?: 'fill' | 'outline';
}

export declare function InlineAlert(props: InlineAlertProps): ReactElement;
