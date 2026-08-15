import type {ReactElement} from 'react';

export interface ProgressCircleProps {
  value?: number;
  size?: 'S' | 'M' | 'L';
  isIndeterminate?: boolean;
  variant?: 'default' | 'overBackground';
}

export declare function ProgressCircle(props: ProgressCircleProps): ReactElement;
