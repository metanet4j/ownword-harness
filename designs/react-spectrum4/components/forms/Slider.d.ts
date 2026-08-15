import type {ReactElement} from 'react';

export interface SliderProps {
  label?: string;
  value?: number;
  defaultValue?: number;
  minValue?: number;
  maxValue?: number;
  step?: number;
  size?: 'S' | 'M' | 'L' | 'XL';
  isDisabled?: boolean;
  onChange?: (value: number) => void;
}

export declare function Slider(props: SliderProps): ReactElement;
