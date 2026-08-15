import type {ReactElement, ReactNode} from 'react';

export interface IllustratedMessageProps {
  children?: ReactNode;
  heading?: string;
  description?: string;
}

export declare function IllustratedMessage(props: IllustratedMessageProps): ReactElement;
