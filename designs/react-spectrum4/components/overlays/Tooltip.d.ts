import type {ReactElement, ReactNode} from 'react';

export interface TooltipProps {
  children?: ReactNode;
  content?: string;
  placement?: 'top' | 'bottom' | 'left' | 'right' | 'start' | 'end';
  isDisabled?: boolean;
}

export declare function Tooltip(props: TooltipProps): ReactElement;
