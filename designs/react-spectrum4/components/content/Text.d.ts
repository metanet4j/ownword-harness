import type {ReactElement, ReactNode} from 'react';

export interface TextProps {
  children?: ReactNode;
  isMuted?: boolean;
}

export declare function Text(props: TextProps): ReactElement;
