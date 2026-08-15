import type {ReactElement, ReactNode} from 'react';

export interface HeadingProps {
  children?: ReactNode;
  level?: 1 | 2 | 3 | 4 | 5 | 6;
}

export declare function Heading(props: HeadingProps): ReactElement;
