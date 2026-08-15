import type {ReactElement, ReactNode} from 'react';

export interface StatusLightProps {
  children?: ReactNode;
  variant?: 'informative' | 'positive' | 'negative' | 'notice' | 'neutral' | 'accent';
  isDisabled?: boolean;
}

export declare function StatusLight(props: StatusLightProps): ReactElement;
