import type {ReactElement} from 'react';

export interface DividerProps {
  orientation?: 'horizontal' | 'vertical';
  size?: 'S' | 'M' | 'L';
}

export declare function Divider(props: DividerProps): ReactElement;
