import type { ChannelType } from './ChannelType';

export interface GeomorphData {
	id: string;
	stream: number;
	ksn: number;
	theta_chi: number;
	theta_sa: number;
	rfit_theta_tt: number;
	error_tt: number;
	rfit_theta_tak: number;
	error_tak: number;
	interpretable: boolean;
	interpret_confidence: number;
	interpretable_user?: boolean;
	channel_type?: ChannelType;
}
