import type {ReactElement} from 'react';

export interface ProgressBarProps {
  label?: string;
  value?: number;
  minValue?: number;
  maxValue?: number;
  size?: 'S' | 'L';
  isIndeterminate?: boolean;
  variant?: 'default' | 'overBackground';
}

export declare function ProgressBar(props: ProgressBarProps): ReactElement;
