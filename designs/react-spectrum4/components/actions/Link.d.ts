import type {ReactElement, ReactNode} from 'react';

export interface LinkProps {
  children?: ReactNode;
  variant?: 'primary' | 'secondary';
  staticColor?: 'white' | 'black';
  isDisabled?: boolean;
  isQuiet?: boolean;
  onPress?: () => void;
}

export declare function Link(props: LinkProps): ReactElement;
