const FULL = new Intl.NumberFormat('en-US');

const K = 1_000;
const M = 1_000_000;
// Above 10M we drop to one-decimal precision (24.5M); below, two decimals (1.50M).
const M_ONE_DECIMAL_THRESHOLD = 10_000_000;

export function fmtFull(n: number): string {
	return FULL.format(n);
}

export function fmtCompact(n: number): string {
	if (n >= M) return (n / M).toFixed(n >= M_ONE_DECIMAL_THRESHOLD ? 1 : 2) + 'M';
	if (n >= K) return (n / K).toFixed(0) + 'K';
	return String(n);
}

const MONTHS_SHORT = [
	'Jan',
	'Feb',
	'Mar',
	'Apr',
	'May',
	'Jun',
	'Jul',
	'Aug',
	'Sep',
	'Oct',
	'Nov',
	'Dec'
];
const DOW_SHORT = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const DOW_LETTER = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];

export function fmtDateLong(date: Date): string {
	return `${DOW_SHORT[date.getUTCDay()]} ${MONTHS_SHORT[date.getUTCMonth()]} ${date.getUTCDate()}, ${date.getUTCFullYear()}`;
}

export function fmtDateShort(date: Date): string {
	return `${DOW_SHORT[date.getUTCDay()]} ${MONTHS_SHORT[date.getUTCMonth()]} ${date.getUTCDate()}`;
}

export function fmtMonthShort(month: number): string {
	return MONTHS_SHORT[month];
}

export function dowLetter(dow: number): string {
	return DOW_LETTER[dow];
}

export function dowShort(dow: number): string {
	return DOW_SHORT[dow];
}
