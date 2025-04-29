/*
 * Program that enumerates volume's NTFS change journal and all
 * its Update Sequence Numbers as well as it's records.
 *
 * MGeeky, Chartham, 2012
 *
 * version 1.0
 */

////////////////////////////////////////

#include <windows.h>
#include <stdio.h>
#include <wchar.h>
#include <winnt.h>
#include <winioctl.h>
#include <getopt.h>

extern int optopt;
extern int opterr;
extern int optind;
extern char* optarg;


////////////////////////////////////////

#define PRINT_LONGLONG( x)	(DWORD)((x) >> 32), (DWORD)(x)

#define FSCTL_QUERY_USN_JOURNAL         CTL_CODE(FILE_DEVICE_FILE_SYSTEM,\
									61, METHOD_BUFFERED, FILE_ANY_ACCESS)

#define FSCTL_READ_USN_JOURNAL          CTL_CODE(FILE_DEVICE_FILE_SYSTEM,\
								46,  METHOD_NEITHER, FILE_ANY_ACCESS)

#define USN_REASON_DATA_OVERWRITE        (0x00000001)
#define USN_REASON_DATA_EXTEND           (0x00000002)
#define USN_REASON_DATA_TRUNCATION       (0x00000004)
#define USN_REASON_NAMED_DATA_OVERWRITE  (0x00000010)
#define USN_REASON_NAMED_DATA_EXTEND     (0x00000020)
#define USN_REASON_NAMED_DATA_TRUNCATION (0x00000040)
#define USN_REASON_FILE_CREATE           (0x00000100)
#define USN_REASON_FILE_DELETE           (0x00000200)
#define USN_REASON_EA_CHANGE             (0x00000400)
#define USN_REASON_SECURITY_CHANGE       (0x00000800)
#define USN_REASON_RENAME_OLD_NAME       (0x00001000)
#define USN_REASON_RENAME_NEW_NAME       (0x00002000)
#define USN_REASON_INDEXABLE_CHANGE      (0x00004000)
#define USN_REASON_BASIC_INFO_CHANGE     (0x00008000)
#define USN_REASON_HARD_LINK_CHANGE      (0x00010000)
#define USN_REASON_COMPRESSION_CHANGE    (0x00020000)
#define USN_REASON_ENCRYPTION_CHANGE     (0x00040000)
#define USN_REASON_OBJECT_ID_CHANGE      (0x00080000)
#define USN_REASON_REPARSE_POINT_CHANGE  (0x00100000)
#define USN_REASON_STREAM_CHANGE         (0x00200000)
#define USN_REASON_TRANSACTED_CHANGE     (0x00400000)
#define USN_REASON_CLOSE                 (0x80000000)

//  Structure for FSCTL_QUERY_USN_JOUNAL

typedef struct {

    ULONGLONG UsnJournalID;
    USN FirstUsn;
    USN NextUsn;
    USN LowestValidUsn;
    USN MaxUsn;
    ULONGLONG MaximumSize;
    ULONGLONG AllocationDelta;

} USN_JOURNAL_DATA, *PUSN_JOURNAL_DATA;


// Structure for FSCTL_READ_USN_JOURNAL

typedef struct {

    USN StartUsn;
    ULONG ReasonMask;
    ULONG ReturnOnlyOnClose;
    ULONGLONG Timeout;
    ULONGLONG BytesToWaitFor;
    ULONGLONG UsnJournalID;

} READ_USN_JOURNAL_DATA, *PREAD_USN_JOURNAL_DATA;


typedef struct {

    ULONG RecordLength;
    USHORT MajorVersion;
    USHORT MinorVersion;
    ULONGLONG FileReferenceNumber;
    ULONGLONG ParentFileReferenceNumber;
    USN Usn;
    LARGE_INTEGER TimeStamp;
    ULONG Reason;
    ULONG SourceInfo;
    ULONG SecurityId;
    ULONG FileAttributes;
    USHORT FileNameLength;
    USHORT FileNameOffset;
    WCHAR FileName[1];

} USN_RECORD, *PUSN_RECORD;


//
// VARIABLES and ROUTINES
//

HANDLE		g_hDrive;

// Specifies which format of timestamp user has specified
// in command line. 0 stands for date, 1 when date and time
// 2 when date, time and miliseconds.
DWORD		g_InputTimeStamp = 0;


// Currently iFlags contains only:
// iFlags = 1 <- show only filenames
BOOL ReadUsnJournal (
		DWORDLONG UsnJournalID,
		DWORDLONG dlMax,
		int iFlags,
		const char *szPattern,
		DWORDLONG dlUSN,
		SYSTEMTIME *stTimeStamp
);

void ParseReason( DWORD dwReason, char* szBuf, unsigned uSize ) ;
void ParseFileAttributes( DWORD dwAttribs, char* szBuf, unsigned uSize );

////////////////////////////////////////

int main( int argc, char** argv)
{
	USN_JOURNAL_DATA		usnJournal = { 0};
	DWORD					dwRet = 0;

	puts ( "\nJournal v1.0 - NTFS change journal records lister\n"
			"Mariusz B., 2012 - MGeeky@gmail.com\n");


	if( argc == 1 || strstr (argv[1], "--h") != NULL
	||	!stricmp ( argv[1], "-h")
	||	!stricmp (argv[1], "/?") )
	{
		printf ("\nUsage:\tjournal [options] <drive>\nWhere:"
				"\n\t<drive>\t\t- is a drive letter with a colon"
				" (i.e. C:)\nOptions:"
				"\n\t-c\t\t- prints only filenames (requires specify"
				" '-d' switch)"
				"\n\t-d\t\t- dump entire journal (huge amount of data!)"
				"\n\t-f <name>\t- find specified <name> in USN entries"
				" filenames"
				"\n\t-t <timestamp>\t- dump records with specified "
				"<timestamp>\n\t\t\t  (hex / yyyy-mm-dd[:hh:MM"
				":ss[.mili]] format,\n\t\t\t  tip: use 99 as a wildcard)\n"
				"\t-u <USN>\t- dump specified <USN> record"
				"\n");
		return 0;
	}

	//
	// PARSING COMMAND LINE
	//

	DWORDLONG dlUSN = 0;
	char szPattern[256] = "";
	char szTmp[32] = "";
	char szDrive[ 10] = "";
	unsigned u = 0;
	SYSTEMTIME stTimeStamp = {0};

	opterr = 0;
	int opt;
	int	dump_journal = 0;
	int only_filenames = 0;


	static struct option opts[] =
	{
		{ "c", no_argument, 0, 'c'},
		{ "d", no_argument, 0, 'd' },
		{ "f", required_argument, 0, 'f'},
		{ "u", required_argument, 0, 'u'},
		{ "t", required_argument, 0, 't'},
		{ 0, 0, 0, 0}
	};

	int ptr;

	while( (opt = getopt_long( argc, argv, "cdf:u:t:", opts, &ptr) ) != -1)
	{
		switch( opt)
		{
			case 'u':
				if( optarg[0] == '0' &&
					(optarg[1] == 'x' || optarg[1] == 'X') )
					optarg += 2;

				if ( strlen(optarg) > 8)
				{
					strncpy( szTmp, optarg, strlen(optarg)-8);
					sscanf( szTmp, "%x", &dlUSN);
					memset (szTmp, 0, sizeof(szTmp));
					strncpy (szTmp, optarg+(strlen(optarg)-8), 8);
					dlUSN <<= 32;
					sscanf( szTmp, "%x", &dlUSN);
				}else
				{
					strncpy( szTmp, optarg, strlen(optarg)-8);
					dlUSN = atol(szTmp);
				}
				break;

			case 'c':
				only_filenames = 1;
				break;

			case 'd':
				dump_journal = 1;
				break;

			case 'f':
				strcpy( szPattern, optarg);
				break;

			case 't':
				if( optarg[0] == '0' &&
					(optarg[1] == 'x' || optarg[1] == 'X') )
					optarg += 2;

				if( strchr(optarg, '-') != NULL)
				{
					SYSTEMTIME st = { 0};

					if( strchr( optarg, ':') != NULL &&
						strchr( optarg, '.') == NULL)
					{
						sscanf(	optarg, "%04d-%02d-%02d:%02d:%02d:%02d",
								&st.wYear, &st.wMonth, &st.wDay,
								&st.wHour, &st.wMinute, &st.wSecond);
						g_InputTimeStamp = 2;
					}
					else if(	strchr( optarg, ':') != NULL &&
								strchr( optarg, '.') != NULL )
					{
						sscanf(	optarg, "%04d-%02d-%02d:%02d:%02d:%02d.%d",
								&st.wYear, &st.wMonth, &st.wDay,
								&st.wHour, &st.wMinute, &st.wSecond,
								&st.wMilliseconds);
						g_InputTimeStamp = 3;
					}
					else
					{
						sscanf(	optarg, "%04d-%02d-%02d", &st.wYear,
								&st.wMonth, &st.wDay );
						g_InputTimeStamp = 1;
					}

					memcpy( &stTimeStamp, &st, sizeof(st) );
				}
				else
				{
					FILETIME ft = { 0};

					if ( strlen(optarg) > 8)
					{
						strncpy( szTmp, optarg, strlen(optarg)-8);
						sscanf( szTmp, "%x", &dlUSN);
						ft.dwLowDateTime = dlUSN;
						dlUSN = 0;
						memset (szTmp, 0, sizeof(szTmp));
						strncpy (szTmp, optarg+(strlen(optarg)-8), 8);
						sscanf( szTmp, "%x", &dlUSN);
						ft.dwHighDateTime = dlUSN;
					}else
					{
						strncpy( szTmp, optarg, strlen(optarg)-8);
						dlUSN = atol(szTmp);
						ft.dwLowDateTime = dlUSN;
					}

					FileTimeToSystemTime( &ft, &stTimeStamp);
					dlUSN = 0;
				}
				break;

			case '?':
				if( optopt == 'f')
					puts ("[!] Option '-f' requires valid pattern!\n");
				else if( optopt == 'u')
					puts ("[!] Option '-u' requires valid USN number!\n");
				else
					printf ("[!] Unknown option '%c'.", optopt);

				return 0;
		}
	}

	for (u=0; u<strlen(argv[argc-1]); u++)
		if (	(argv[argc-1][u] >= 'a' && argv[argc-1][u] <= 'z') ||
				(argv[argc-1][u] >= 'A' && argv[argc-1][u] <= 'Z') )
		{
			if( argv[argc-1][u+1] == ':')
			{
				sprintf( szDrive, "\\\\.\\%c:", argv[argc-1][u]);
				break;
			}
			else
			{
				puts ("[!] You haven't specified <drive> to use.");
				return 0;
			}
		}


	//
	// EXAMINING DRIVE
	//

	printf( "\n[?] Examining %s drive's journal...\n", szDrive);

	g_hDrive = CreateFileA( szDrive,
							GENERIC_READ,
							FILE_SHARE_READ|FILE_SHARE_WRITE,
							NULL,
							OPEN_EXISTING,
							FILE_ATTRIBUTE_NORMAL,
							NULL);
	if( g_hDrive == (HANDLE)-1 )
	{
		printf ("[!] Cannot open drive: %d", GetLastError() );
		return 0;
	}

	if( !DeviceIoControl(	g_hDrive,
							FSCTL_QUERY_USN_JOURNAL,
							NULL,
							0,
							&usnJournal,
							sizeof( usnJournal),
							&dwRet,
							NULL))
	{
		DWORD dwErr = GetLastError();

		switch( dwErr)
		{
			case ERROR_JOURNAL_NOT_ACTIVE:
				printf ("[!] Drive's journal hasn't been"
						" activated so far.");
				break;

			default:
			printf ("[!] Couldn't query USN journal: %d",
					GetLastError() );
		}
		return 0;
	}


	// Dump JOURNAL DATA
	printf ("\nJournal data for %s drive\n"
			"\tUsnJournalID =\t\t%08x%08x\n"
			"\tFirstUsn =\t\t%08x%08x\n"
			"\tNextUsn =\t\t%08x%08x\n"
			"\tLowestValidUsn =\t%08x%08x\n"
			"\tMaxUsn =\t\t%08x%08x\n"
			"\tMaximumSize =\t\t%08x%08x\n"
			"\tAllocationDelta =\t%08x%08x\n\n",
			szDrive,
			PRINT_LONGLONG( usnJournal.UsnJournalID),
			PRINT_LONGLONG( usnJournal.FirstUsn),
			PRINT_LONGLONG( usnJournal.NextUsn),
			PRINT_LONGLONG( usnJournal.LowestValidUsn),
			PRINT_LONGLONG( usnJournal.MaxUsn),
			PRINT_LONGLONG( usnJournal.MaximumSize),
			PRINT_LONGLONG( usnJournal.AllocationDelta) );


	if( dlUSN != 0)
	{
		printf ("[>] Searching for records with USN = %x%x\n\n",
				PRINT_LONGLONG( dlUSN));

		ReadUsnJournal (usnJournal.UsnJournalID,
						(usnJournal.FirstUsn - usnJournal.NextUsn),
						only_filenames, NULL, dlUSN, NULL);
	}else if( strlen( szPattern) )
	{
		printf ("[>] Searching for records with pattern = %s\n\n",
				szPattern);

		ReadUsnJournal (usnJournal.UsnJournalID,
						(usnJournal.FirstUsn - usnJournal.NextUsn),
						only_filenames, szPattern, 0, NULL);
	}else if( dump_journal == 1)
		ReadUsnJournal (usnJournal.UsnJournalID,
						(usnJournal.FirstUsn - usnJournal.NextUsn),
						only_filenames, NULL, 0, NULL);
	else if( g_InputTimeStamp > 0 )
	{
		printf ("[>] Searching for records from %04d-%02d-%02d",
				stTimeStamp.wYear, stTimeStamp.wMonth, stTimeStamp.wDay);

		if( g_InputTimeStamp == 2)
			printf ( " %02d:%02d:%02d", stTimeStamp.wHour,
					stTimeStamp.wMinute, stTimeStamp.wSecond);

		if( g_InputTimeStamp == 3)
			printf ( ".%d", stTimeStamp.wMilliseconds );

		puts("\n");

		ReadUsnJournal (usnJournal.UsnJournalID,
						(usnJournal.FirstUsn - usnJournal.NextUsn),
						only_filenames, NULL, 0, &stTimeStamp);
	}

	CloseHandle( g_hDrive);


	return 0;

}


////////////////////////////////////////

BOOL ReadUsnJournal (
		DWORDLONG UsnJournalID,
		DWORDLONG dlMax,
		int iFlags,
		const char* szPattern,
		DWORDLONG dlUSN,
		SYSTEMTIME *stTimeStamp
)
{

	READ_USN_JOURNAL_DATA	usnReadData = { 0};
	PUSN_RECORD				pUsnRecord;
	CHAR					cBuf[ 4096] = {0};
	DWORD					dwRet = 0;
	DWORD					nUSN = 0;
	DWORD					nEntry = 0;
	DWORDLONG				nOverall = 0;
	WCHAR					wsPattern[256] = L"";
	unsigned				bOnce = 0;

	if( szPattern != NULL)
		mbstowcs( wsPattern, szPattern, strlen(szPattern));


	// Select every possible entry in the journal
	usnReadData.ReasonMask = 0xFFFFFFFF;

	usnReadData.UsnJournalID = UsnJournalID;
	usnReadData.BytesToWaitFor = 200;
	usnReadData.Timeout = 5;

	// Iterate on USNs
	while( 1)
	{
		memset( cBuf, 0, sizeof (cBuf));

		if( !DeviceIoControl (	g_hDrive,
								FSCTL_READ_USN_JOURNAL,
								&usnReadData,
								sizeof(usnReadData),
								cBuf,
								sizeof( cBuf),
								&dwRet,
								NULL))
		{
			printf ("[!] Reading USN Journal for %ld failed: %d",
					UsnJournalID, GetLastError() );
			break;
		}

		if( dwRet < 256 )
			break;

		dwRet -= sizeof(USN);

		// Find the first record in the journal
		pUsnRecord = (PUSN_RECORD)(((PUCHAR)cBuf) + sizeof(USN) );

		if( dlUSN == 0 && szPattern == NULL
			&& stTimeStamp == NULL && iFlags != 1 )
			printf ("******************************************\n");

		nEntry = 0;

		// Iterate on USN's records
		while(dwRet > 0)
		{
			int bValidTimeStamp = 0;
			FILETIME ft = { 0};
			SYSTEMTIME st = {0};

			ft.dwLowDateTime = pUsnRecord->TimeStamp.LowPart;
			ft.dwHighDateTime = pUsnRecord->TimeStamp.HighPart;

			FileTimeToSystemTime( &ft, &st);

		#define CHECK(x,y) (((x) == 99)? 1 : (x) == (y) )

			// Check if record's timestamp corresponds to the
			// specified by user timestamp
			if( stTimeStamp != NULL)
			{
				if( stTimeStamp->wYear == st.wYear &&
					CHECK(stTimeStamp->wMonth, st.wMonth) &&
					CHECK(stTimeStamp->wDay, st.wDay) )
				{
					if( g_InputTimeStamp == 1)
						bValidTimeStamp = 1;

					else if( g_InputTimeStamp >= 2 &&
							CHECK(stTimeStamp->wHour, st.wHour) &&
							CHECK(stTimeStamp->wMinute, st.wMinute) &&
							CHECK(stTimeStamp->wSecond, st.wSecond))
					{
						if( g_InputTimeStamp == 2)
							bValidTimeStamp = 1;

						else if( g_InputTimeStamp == 3 &&
								stTimeStamp->wMilliseconds ==
									st.wMilliseconds)
							bValidTimeStamp = 1;
					}
				}
			}

		#undef CHECK


			// Checking if specified conditions have been met.
			if( (szPattern != NULL
				&& (wcsstr(pUsnRecord->FileName, wsPattern)!=NULL) )
			||	(dlUSN != 0 && pUsnRecord->Usn == dlUSN)
			||	(dlUSN == 0 && szPattern == NULL && stTimeStamp == NULL)
			||	(stTimeStamp != NULL && bValidTimeStamp == 1 ) )
			{
				if( iFlags == 1)
				{
					wprintf(	L"%.*ls\n",
								pUsnRecord->FileNameLength/2,
								pUsnRecord->FileName
						   );
				}
				else
				{
					char szReason[256] = "";
					char szFileAttribs[256] = "";

					// FileReferenceNumber contains Sequence number
					// in 16 most significant bits. We gotta wipe
					// them out to extract only lower 48 bits of
					// MFT file record's index.
					DWORDLONG dlMFTidx = pUsnRecord->FileReferenceNumber;
					dlMFTidx <<= 16;
					dlMFTidx >>= 16;

					ParseReason(	pUsnRecord->Reason, szReason,
									sizeof( szReason));

					ParseFileAttributes( pUsnRecord->FileAttributes,
									szFileAttribs, sizeof( szFileAttribs));

					wprintf (	"\n%x%x/%d.%d: (ret=%d)\n"
								L"\tUSN = %08x%08x\n"
								L"\tFileReferenceNumber = %x%x "
								L"(MFT's idx: %lu)\n"
								L"\tFileName = %.*ls\n"
								L"\tTimeStamp = %x%x"
								" (%04d-%02d-%02d %02d:%02d:%02d.%d)\n"
								L"\tSecurityID = %x\n",
								PRINT_LONGLONG( nOverall),
								nUSN, nEntry, dwRet,
								PRINT_LONGLONG( pUsnRecord->Usn),
								PRINT_LONGLONG( pUsnRecord\
									->FileReferenceNumber),
								(DWORD)dlMFTidx,	// LOSS OF DATA !!
								pUsnRecord->FileNameLength/2,
								pUsnRecord->FileName,
							PRINT_LONGLONG( pUsnRecord->TimeStamp.QuadPart),
								st.wYear, st.wMonth, st.wDay, st.wHour,
								st.wMinute, st.wSecond, st.wMilliseconds,
								pUsnRecord->SecurityId
					);

					printf (	"\tFileAttributes = 0x%X\n%s\n"
								"\tReason = 0x%X\n%s\n",
								pUsnRecord->FileAttributes,
								szFileAttribs,
								pUsnRecord->Reason,
								szReason
					);
				}

				if( dlUSN != 0)
					return TRUE;
			}

			nEntry += 1;
			nOverall += 1;

			dwRet -= pUsnRecord->RecordLength;

			// Find the next record
			pUsnRecord = (PUSN_RECORD)( ((PCHAR)pUsnRecord) + \
									pUsnRecord->RecordLength);
		}

		// Update starting USN for next call
		usnReadData.StartUsn = *(USN*)&cBuf;

		nUSN += 1;
	}

	return TRUE;
}


///////////////////////////////////////

void ParseReason( DWORD dwReason, char* szBuf, unsigned uSize )
{

	if (dwReason & USN_REASON_BASIC_INFO_CHANGE )
		strcat (szBuf, "\t\tUSN_REASON_BASIC_INFO_CHANGE |\n");
	if (dwReason & USN_REASON_CLOSE )
		strcat (szBuf, "\t\tUSN_REASON_CLOSE |\n");
	if (dwReason & USN_REASON_COMPRESSION_CHANGE )
		strcat (szBuf, "\t\tUSN_REASON_COMPRESSION_CHANGE |\n");
	if (dwReason & USN_REASON_DATA_EXTEND )
		strcat (szBuf, "\t\tUSN_REASON_DATA_EXTEND |\n");
	if (dwReason & USN_REASON_DATA_OVERWRITE )
		strcat (szBuf, "\t\tUSN_REASON_DATA_OVERWRITE |\n");
	if (dwReason & USN_REASON_DATA_TRUNCATION )
		strcat (szBuf, "\t\tUSN_REASON_DATA_TRUNCATION |\n");
	if (dwReason & USN_REASON_EA_CHANGE )
		strcat (szBuf, "\t\tUSN_REASON_EA_CHANGE |\n");
	if (dwReason & USN_REASON_ENCRYPTION_CHANGE )
		strcat (szBuf, "\t\tUSN_REASON_ENCRYPTION_CHANGE |\n");
	if (dwReason & USN_REASON_FILE_CREATE )
		strcat (szBuf, "\t\tUSN_REASON_FILE_CREATE |\n");
	if (dwReason & USN_REASON_FILE_DELETE )
		strcat (szBuf, "\t\tUSN_REASON_FILE_DELETE |\n");
	if (dwReason & USN_REASON_HARD_LINK_CHANGE )
		strcat (szBuf, "\t\tUSN_REASON_HARD_LINK_CHANGE |\n");
	if (dwReason & USN_REASON_INDEXABLE_CHANGE )
		strcat (szBuf, "\t\tUSN_REASON_INDEXABLE_CHANGE |\n");
	if (dwReason & USN_REASON_NAMED_DATA_EXTEND )
		strcat (szBuf, "\t\tUSN_REASON_NAMED_DATA_EXTEND |\n");
	if (dwReason & USN_REASON_NAMED_DATA_OVERWRITE )
		strcat (szBuf, "\t\tUSN_REASON_NAMED_DATA_OVERWRITE |\n");
	if (dwReason & USN_REASON_NAMED_DATA_TRUNCATION )
		strcat (szBuf, "\t\tUSN_REASON_NAMED_DATA_TRUNCATION |\n");
	if (dwReason & USN_REASON_OBJECT_ID_CHANGE )
		strcat (szBuf, "\t\tUSN_REASON_OBJECT_ID_CHANGE |\n");
	if (dwReason & USN_REASON_RENAME_NEW_NAME )
		strcat (szBuf, "\t\tUSN_REASON_RENAME_NEW_NAME |\n");
	if (dwReason & USN_REASON_RENAME_OLD_NAME )
		strcat (szBuf, "\t\tUSN_REASON_RENAME_OLD_NAME |\n");
	if (dwReason & USN_REASON_REPARSE_POINT_CHANGE )
		strcat (szBuf, "\t\tUSN_REASON_REPARSE_POINT_CHANGE |\n");
	if (dwReason & USN_REASON_SECURITY_CHANGE )
		strcat (szBuf, "\t\tUSN_REASON_SECURITY_CHANG |\n");
	if (dwReason & USN_REASON_STREAM_CHANGE )
		strcat (szBuf, "\t\tUSN_REASON_STREAM_CHANG |\n");

	szBuf[ strlen(szBuf)-3] = 0;
}


///////////////////////////////////////

void ParseFileAttributes( DWORD dwAttribs, char* szBuf, unsigned uSize )
{

	if( dwAttribs & FILE_ATTRIBUTE_READONLY )
		strcat (szBuf, "\t\tFILE_ATTRIBUTE_READONLY |\n");
	if( dwAttribs & FILE_ATTRIBUTE_HIDDEN )
		strcat (szBuf, "\t\tFILE_ATTRIBUTE_HIDDEN |\n");
	if( dwAttribs & FILE_ATTRIBUTE_SYSTEM )
		strcat (szBuf, "\t\tFILE_ATTRIBUTE_SYSTEM |\n");
	if( dwAttribs & FILE_ATTRIBUTE_DIRECTORY )
		strcat (szBuf, "\t\tFILE_ATTRIBUTE_DIRECTORY |\n");
	if( dwAttribs & FILE_ATTRIBUTE_ARCHIVE )
		strcat (szBuf, "\t\tFILE_ATTRIBUTE_ARCHIVE |\n");
	if( dwAttribs & FILE_ATTRIBUTE_DEVICE )
		strcat (szBuf, "\t\tFILE_ATTRIBUTE_DEVICE |\n");
	if( dwAttribs & FILE_ATTRIBUTE_NORMAL )
		strcat (szBuf, "\t\tFILE_ATTRIBUTE_NORMAL |\n");
	if( dwAttribs & FILE_ATTRIBUTE_TEMPORARY )
		strcat (szBuf, "\t\tFILE_ATTRIBUTE_TEMPORARY |\n");
	if( dwAttribs & FILE_ATTRIBUTE_SPARSE_FILE )
		strcat (szBuf, "\t\tFILE_ATTRIBUTE_SPARSE_FILE |\n");
	if( dwAttribs & FILE_ATTRIBUTE_REPARSE_POINT )
		strcat (szBuf, "\t\tFILE_ATTRIBUTE_REPARSE_POINT |\n");
	if( dwAttribs & FILE_ATTRIBUTE_COMPRESSED )
		strcat (szBuf, "\t\tFILE_ATTRIBUTE_COMPRESSED |\n");
	if( dwAttribs & FILE_ATTRIBUTE_OFFLINE )
		strcat (szBuf, "\t\tFILE_ATTRIBUTE_OFFLINE |\n");
	if( dwAttribs & FILE_ATTRIBUTE_NOT_CONTENT_INDEXED )
		strcat (szBuf, "\t\tFILE_ATTRIBUTE_NOT_CONTENT_INDEXED |\n");
	if( dwAttribs & FILE_ATTRIBUTE_ENCRYPTED )
		strcat (szBuf, "\t\tFILE_ATTRIBUTE_ENCRYPTED |\n");
	if( dwAttribs & FILE_ATTRIBUTE_VALID_FLAGS )
		strcat (szBuf, "\t\tFILE_ATTRIBUTE_VALID_FLAGS |\n");
	if( dwAttribs & FILE_ATTRIBUTE_VALID_SET_FLAGS )
		strcat (szBuf, "\t\tFILE_ATTRIBUTE_VALID_SET_FLAGS |\n");

	szBuf[ strlen(szBuf)-3] = 0;
}
