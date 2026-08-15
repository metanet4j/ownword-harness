import type {ReactElement, ReactNode} from 'react';

export interface AvatarProps {
  children?: ReactNode;
  src?: string;
  alt?: string;
  size?: 'S' | 'M' | 'L';
}

export declare function Avatar(props: AvatarProps): ReactElement;
