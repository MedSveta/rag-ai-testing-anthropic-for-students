import pytest

MIN_RELEVANCE_SCORE = 0.35


def retrieve(api_client, question, top_k=4):
    response = api_client.post("/retrieve", json={"question": question, "top_k": top_k})
    assert response.status_code == 200, response.text
    return response.json()["contexts"]


def found_requirement_ids(contexts):
    res = set()
    for context in contexts:
        for rid in context["requirement_ids"]:
            res.add(rid)
    return res


@pytest.mark.parametrize(
    ("question", "expected_id"),
    [pytest.param("What is the minimum customer password length?", "T14", id="min-length-password"),
     pytest.param("What is the maximum customer password length?", "T15", id="max-length-password"),
     pytest.param("Is the number required in password length?", "T13", id="numbers-in-password"),
     pytest.param("What is the language in the customer password?", "T10", id="password-language"),
     pytest.param("Is a special character required in the customer password?", "T9", id="password-special-characters"),
     pytest.param("Is customer email required?", "T1", id="email-required"),
     pytest.param("How many @ may be in customer email?", "T3", id="email-at"),
     pytest.param("How many characters i need before @ in the customer email?", "T4", id="email-form-before-at"),
     ],
)
def test_retrieve_question(api_client, question, expected_id):
    contexts = retrieve(api_client, question)
    assert expected_id in found_requirement_ids(contexts)


@pytest.mark.parametrize(
    ("question", "expected_id"),
    [pytest.param("What is the minimum customer password length?", "T14", id="min-length-password"),
     pytest.param("What is the maximum customer password length?", "T15", id="max-length-password"),
     pytest.param("Is the number required in password length?", "T13", id="numbers-in-password"),
     pytest.param("What is the language in the customer password?", "T10", id="password-language"),
     pytest.param("Is a special character required in the customer password?", "T9", id="password-special-characters"),
     pytest.param("Is customer email required?", "T1", id="email-required"),
     pytest.param("How many @ may be in customer email?", "T3", id="email-at"),
     ],
)
def test_retrieve_expected_id_is_first(api_client, question, expected_id):
    contexts = retrieve(api_client, question)
    assert len(contexts) > 0, "Not found contexts"
    assert expected_id in contexts[0]["requirement_ids"]


@pytest.mark.parametrize(
    "question",
    [pytest.param("What is my name?", id="my-name"),
     pytest.param("What is the day today?", id="day-today"),
     pytest.param("Who is my mum?", id="who-is"),
     ],
)
def test_retrieve_question_incorrect(api_client, question):
    contexts = retrieve(api_client, question)
    assert contexts ==[]

@pytest.mark.parametrize(
    "question",
    [pytest.param("What is the minimum customer password length?", id="original"),
     pytest.param("How many characters must a customer password have at least?", id="perefrasilovaly"),
     pytest.param("WHAT IS THE MINIMUM CUSTOMER PASSWORD LENGTH?", id="upper-case"),
     pytest.param("minimum customer password?", id="password-language"),
     ],
)
def test_retrieve_question_find_simular_words(api_client, question):
    contexts = retrieve(api_client, question)
    assert "T14" in found_requirement_ids(contexts)


def test_retrieve_same_question_return_same_result(api_client):
    question = "What is the minimum customer password length?"
    first = retrieve(api_client, question)
    second = retrieve(api_client, question)

    assert [c["chunk_id"] for c in first] == [c["chunk_id"] for c in second]
    assert [c["score"] for c in first] == [c["score"] for c in second]

@pytest.mark.xfail(
    reason=("Известный баг поиска: T41/42"
            " или T79/80 приходит chunk F8"
            ),
    strict=False,
)
def test_retrieve_length_phone(api_client):
    contexts = retrieve(api_client, "What length is allowed for a contact phone number?")
    assert {"T41", "T42"} in found_requirement_ids(contexts)

@pytest.mark.xfail(
    reason=("Известный баг поиска: T4"
            " приходит id T5"
            ),
    strict=False,
)
def test_retrieve_expected_t4_is_first(api_client):
    expected_id = "T4"
    contexts = retrieve(api_client, "How many characters i need before @ in the customer email?")

    assert expected_id in contexts[0]["requirement_ids"]


@pytest.mark.xfail(
    reason=("Модель эмбеддингов не обучена другому языку"
            ),
    strict=False,
)
def test_question_in_russian_find_requirements(api_client):
    contexts = retrieve(api_client, "Какая максимальная длина пароля у клиента?")
    assert "T15" in found_requirement_ids(contexts)





