import pandas as pd
from pathlib import Path
from src.etl_extract_transform import read_one_xml, build_dims
from src.validate import validate_fact

def test_parse_sample():
    fp = Path("data/raw/trades_august.xml")
    df = read_one_xml(str(fp))
    assert not df.empty
    assert {"reporter_iso2","partner_iso2","commodity_code"}.issubset(df.columns)

def test_transform_and_validate():
    df = pd.concat([read_one_xml("data/raw/trades_august.xml"),
                    read_one_xml("data/raw/trades_september.xml")], ignore_index=True)
    _, _, _, fact = build_dims(df)
    fact = validate_fact(fact)
    assert "bk" in fact.columns and fact["bk"].nunique() == len(fact)
