""" Create Spreadsheet from raw netbox data """


from logging import getLogger
from typing import List, Optional

getLogger('googleapiclient').setLevel(0)
getLogger().setLevel(0)


class DictMask(dict):
    """ Create dict from any object """

    def __init__(self, *args, **kw) -> None:
        """ Init """
        none_less_args = [v for v in args if v is not None]
        none_less_kw   = {k: v for k, v in kw.items() if v is not None}

        super().__init__(*none_less_args, **none_less_kw)
        # super().__init__(*args, **kw)
        self.itemlist = super().keys()

    def __setitem__(self, key, value):
        self.itemlist.append(key)
        super().__setitem__(key, value)

    def __iter__(self):
        return enumerate(self.itemlist)

    def keys(self):
        return self.itemlist

    def values(self):
        return [self[key] for key in self]

    def itervalues(self):
        return (self[key] for key in self)


class ExtendedValue(DictMask):
    def __init__(self,
                 value=None,
                 numberValue=None,
                 stringValue=None,
                 boolValue=None,
                 formulaValue=None) -> None:
        """ Init """
        if type(value) in [float, int]:
            self.numberValue = value
        elif type(value) is str:
            self.stringValue = value
        elif numberValue is not None:
            self.numberValue = numberValue
        elif type(value) is bool:
            self.boolValue: bool = value
        elif hasattr(self, "boolValue") and self.boolValue is not None:
            self.boolValue = boolValue
        elif formulaValue is not None:
            self.formulaValue: str = formulaValue
        elif stringValue is not None:
            self.stringValue: str = stringValue
        # self.errorValue: { ErrorValue }
        super().__init__(self.__dict__)



class GridRange(DictMask):
    """ Range of data

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets#GridRange
    """

    def __init__(self,
                 startRowIndex: int = 0,
                 endRowIndex: int = None,
                 startColumnIndex: int = 0,
                 endColumnIndex: int = None,
                 sheetId: int = None) -> None:
        """ Init """
        # self.sheetId: int           = sheetId
        self.startRowIndex: int             = startRowIndex
        self.endRowIndex: Optional[int]     = endRowIndex if endRowIndex is not None else startRowIndex
        self.startColumnIndex: int          = startColumnIndex
        self.endColumnIndex: Optional[int]  = endColumnIndex if endRowIndex is not None else startColumnIndex
        super().__init__(self.__dict__)


class ConditionType(DictMask):
    """ Enum, type of condition """

    CONDITION_TYPE_UNSPECIFIED = 0x00
    NUMBER_GREATER             = 0x01
    NUMBER_GREATER_THAN_EQ     = 0x02
    NUMBER_LESS                = 0x03
    NUMBER_LESS_THAN_EQ        = 0x04
    NUMBER_EQ                  = 0x05
    NUMBER_NOT_EQ              = 0x06
    NUMBER_BETWEEN             = 0x07
    NUMBER_NOT_BETWEEN         = 0x08
    TEXT_CONTAINS              = 0x09
    TEXT_NOT_CONTAINS          = 0x0A
    TEXT_STARTS_WITH           = 0x0B
    TEXT_ENDS_WITH             = 0x0C
    TEXT_EQ                    = 0x0D
    TEXT_IS_EMAIL              = 0x0E
    TEXT_IS_URL                = 0x0F
    DATE_EQ                    = 0x10
    DATE_BEFORE                = 0x12
    DATE_AFTER                 = 0x13
    DATE_ON_OR_BEFORE          = 0x14
    DATE_ON_OR_AFTER           = 0x15
    DATE_BETWEEN               = 0x16
    DATE_NOT_BETWEEN           = 0x17
    DATE_IS_VALID              = 0x18
    ONE_OF_RANGE               = 0x19
    ONE_OF_LIST                = 0x1A
    BLANK                      = 0x1B
    NOT_BLANK                  = 0x1C
    CUSTOM_FORMULA             = 0x1D
    BOOLEAN                    = 0x1E


class RelativeDate(DictMask):
    """ Controls how a date is evaluated """

    RELATIVE_DATE_UNSPECIFIED = 0x00
    PAST_YEAR                 = 0x01
    PAST_MONTH                = 0x02
    PAST_WEEK                 = 0x03
    YESTERDAY                 = 0x04
    TODAY                     = 0x05
    TOMORROW                  = 0x06


class ConditionValue(DictMask):
    """ Value of a condition """

    def __init__(self,
                 relativeDate: Optional[RelativeDate] = None,
                 userEnteredValue: Optional[str] = None ) -> None:
        self.relativeDate = relativeDate
        self.userEnteredValue = userEnteredValue
        super().__init__(self.__dict__)



class BooleanCondition(DictMask):
    """ Condition that the data must match """
    def __init__(self,
                 type: Optional[ConditionType] = None,
                 values: Optional[List[ConditionValue]] = None ) -> None:
        if type is not None:
            self.type   = type
        if values is not None:
            self.values = values
        super().__init__(self.__dict__)



class DataValidationRule(DictMask):
    """ A data validation rule.

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets#DataValidationRule
    """

    def __init__(self,
                 condition: BooleanCondition = BooleanCondition(),
                 inputMessage: Optional[str] = None,
                 strict: Optional[bool] = None,
                 showCustomUi: Optional[bool] = None ) -> None:
        
        if condition is not None:
            self.condition    = condition
        if inputMessage is not None:
            self.inputMessage = inputMessage
        if strict is not None:
            self.strict       = strict
        if showCustomUi is not None:
            self.showCustomUi = showCustomUi
        super().__init__(self.__dict__)



class Color(DictMask):
    def __init__(self,
                 red: int = 0,
                 green: int = 0,
                 blue: int = 0,
                 alpha: int = 0) -> None:
        """ Init """
        self.red:   int = red
        self.green: int = green
        self.blue:  int = blue
        self.alpha: int = alpha
        super().__init__(self.__dict__)



class CellData(DictMask):
    """ Container for data and metadata within a cell

    Data about a specific cell.
    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets#celldata
    """

    def __init__(self,
                 userEnteredValue: Optional[ExtendedValue] = None,
                 effectiveValue: Optional[ExtendedValue] = None,
                 formattedValue: Optional[str] = None,
                 userEnteredFormat = None,
                 effectiveFormat = None,
                 hyperlink: Optional[str] = None,
                 note: Optional[str] = None,
                 textFormatRuns = None,
                 dataValidation: Optional[DataValidationRule] = None,
                 pivotTable = None) -> None:
        """ Init """
        if type(userEnteredValue) is not ExtendedValue:
            raise TypeError(f"userEnteredValue parameter on CellData must be of type ExtendedValue not {type(userEnteredValue)}")
        self.userEnteredValue: Optional[ExtendedValue] = userEnteredValue
        if effectiveValue is not None:
            self.effectiveValue: Optional[ExtendedValue] = effectiveValue
        if formattedValue is not None:
            self.formattedValue: Optional[str] = formattedValue
        # userEnteredFormat: {CellFormat}
        # effectiveFormat: {CellFormat}
        if hyperlink is not None:
            self.hyperlink: Optional[str] = hyperlink
        if note is not None:
            self.note: Optional[str] = note
        #   textFormatRuns: [ { TextFormatRun } ]
        if dataValidation is not None:
            self.dataValidation: Optional[DataValidationRule] = dataValidation
        #   pivotTable: { PivotTable }
        super().__init__(self.__dict__)



class RowData(DictMask):
    """ Value Container for a Row of CellData

    Data about each cell in a row.
    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets#rowdata
    """

    def __init__(self, values: List[CellData]) -> None:
        """ Create an instance of RowData

        values should be CellData[]
            a list of CellData
        """
        if type(values) is not list:
            raise TypeError("values for RowData _must_ be of type list")
        self.values: List[CellData] = values
        super().__init__(self.__dict__)



class GridData(DictMask):
    """ Data in the grid, as well as metadata about the dimensions

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets#griddata
    """

    def __init__(self,
                 startRow: int = 0,
                 startColumn: int = 0,
                 rowData: List[RowData] = []) -> None:
        """ Init """
        if type(startRow) is not int:
            raise TypeError(f"startRow parameter on {self.__class__.__name__} must be of type int not {type(startRow)}")
        if type(startColumn) is not int:
            raise TypeError(f"startColumn parameter on {self.__class__.__name__} must be of type int not {type(startColumn)}")
        if type(rowData) is not list:
            raise TypeError(f"RowData parameter on {self.__class__.__name__} must be of type list not {type(rowData)}")
        self.startRow:    int       = startRow
        self.startColumn: int       = startColumn
        if len(rowData) > 0:
            if type(rowData[0]) is not RowData:
                raise TypeError(f"RowData parameter on {self.__class__.__name__} must be of be list containing objects of type RowData not {type(rowData[0])}")
            self.rowData:     List[RowData] = rowData
        # self.rowMetadata: [DimensionProperties]
        # self.columnMetadata: [DimensionProperties]
        super().__init__(self.__dict__)



class BandingProperties(DictMask):
    def __init__(self,
                 headerColor: Color = Color(),
                 footerColor: Color = Color(),
                 firstBandColor: Color = Color(),
                 secondBandColor: Color = Color()) -> None:
        """ Init """
        self.headerColor: Color     = headerColor
        self.footerColor: Color     = footerColor
        self.firstBandColor: Color  = firstBandColor
        self.secondBandColor: Color = secondBandColor
        super().__init__(self.__dict__)



class BandedRange(DictMask):
    """ BandedRange is alternating row colors

                 range:            GridRange         = GridRange()
                 rowProperties:    BandingProperties = BandingProperties()
                 columnProperties: BandingProperties = BandingProperties()
                 id:               int               = None
    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets#BandedRange
    """

    bandedRangeId_sequence = 0

    def __init__(self,
                 range: GridRange = GridRange(),
                 rowProperties: BandingProperties = BandingProperties(),
                 columnProperties: BandingProperties = BandingProperties(),
                 bandedRangeId: Optional[int] = None) -> None:
        """ Init """
        if type(bandedRangeId) is not int:
            bandedRangeId = BandedRange.bandedRangeId_sequence
            BandedRange.bandedRangeId_sequence = BandedRange.bandedRangeId_sequence + 1
        self.bandedRangeId: int                     = bandedRangeId
        self.range: GridRange                       = range
        self.rowProperties: BandingProperties       = rowProperties
        self.columnProperties: BandingProperties    = columnProperties
        super().__init__(self.__dict__)



class SpreadsheetProperties(DictMask):
    def __init__(self,
                 title: str = "netbox-export-cabling",
                 locale: str = "en_US",
                 #  autoRecalc: RecalculationInterval
                 timeZone: str = "America/Los_Angeles"
                 # defaultFormat: CellFormat,
                 # iterativeCalculationSettings: iterativeCalculationSettings
                 ) -> None:
        """ Init """
        self.title = title

        super().__init__(self.__dict__)


class ConditionalFormatRule(DictMask):

    def __init__(self) -> None:
        """ Init """
        pass


class ProtectedRange(DictMask):

    def __init__(self) -> None:
        """ Init """
        pass


class BasicFilter(DictMask):

    def __init__(self) -> None:
        """ Init """
        pass


class FilterView(DictMask):

    def __init__(self) -> None:
        """ Init """
        pass


class EmbeddedChart(DictMask):

    def __init__(self) -> None:
        """ Init """
        pass


class NamedRange(DictMask):

    def __init__(self) -> None:
        """ Init """
        pass


class DimensionGroup(DictMask):

    def __init__(self) -> None:
        """ Init """
        pass


class DeveloperMetadata(DictMask):

    def __init__(self) -> None:
        """ Init """
        pass


class Sheet(DictMask):
    def __init__(self,
                 data: List[GridData] = [],
                 bandedRanges: List[BandedRange] = [],
                 merges: List[GridRange] = [],
                 #  conditionalFormats: [ConditionalFormatRule] = [],
                 #  filterViews: [FilterView] = [],
                 #  protectedRanges: [ProtectedRange] = [],
                 # #  basicFilter: BasicFilter = BasicFilter(),
                 #  charts: [EmbeddedChart] = [],
                 #  rowGroups: [DimensionGroup] = [],
                 #  columnGroups: [DimensionGroup] = [],
                 # #  properties: SpreadsheetProperties = SpreadsheetProperties(),
                 #  developerMetadata: [DeveloperMetadata] = []
                 ) -> None:
        """ Init """
        self.data: List[GridData] = data
        # self.merges: [GridRange] = merges
        self.bandedRanges: List[BandedRange] = bandedRanges
        # self.conditionalFormats: [ConditionalFormatRule] = conditionalFormats
        # self.filterViews: [FilterView] = filterViews
        # self.protectedRanges: [ProtectedRange] = protectedRanges
        # # self.basicFilter: BasicFilter = basicFilter
        # self.charts: [EmbeddedChart] = charts
        # self.rowGroups: [DimensionGroup] = rowGroups
        # self.columnGroups: [DimensionGroup] = columnGroups
        # # self.properties: SpreadsheetProperties = properties
        # self.developerMetadata: [DeveloperMetadata] = developerMetadata
        super().__init__(self.__dict__)




# class Sheet(DictMask):

#     def __init__(self, one="this", two="that"):
#         self.one = one
#         self.two = two

#         # print(f"self.one={self.one}")
#         # print(f"self.two={self.two}")
#         super().__init__(self.__dict__)




class Spreadsheet(DictMask):
    def __init__(self,
                 sheets: List[Sheet] = [],
                 spreadsheetId="",
                 properties: SpreadsheetProperties = None,
                 namedRange: List[NamedRange] = NamedRange(),
                 spreadsheetUrl: str = "",
                 developerMetadata: DeveloperMetadata = DeveloperMetadata()) -> None:
        """ Create Spreadsheet instance """
        # self.spreadsheetId: str = spreadsheetId
        if properties is not None:
            self.properties: SpreadsheetProperties = properties
        self.sheets: List[Sheet] = sheets
        self.namedRanged: List[NamedRange]
        self.spreadsheetUrl: str
        self.developerMetadata: List[DeveloperMetadata]
        super().__init__(self.__dict__)



