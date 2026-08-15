import type {ReactElement} from 'react';

export interface CloseButtonProps {
  size?: 'S' | 'M' | 'L' | 'XL';
  isDisabled?: boolean;
  staticColor?: 'white' | 'black';
  'aria-label'?: string;
}

export declare function CloseButton(props: CloseButtonProps): ReactElement;
