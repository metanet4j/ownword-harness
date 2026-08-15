import type {ReactElement, ReactNode} from 'react';

export interface ToastProps {
  children?: ReactNode;
  variant?: 'neutral' | 'informative' | 'positive' | 'negative';
}

export declare function Toast(props: ToastProps): ReactElement;
